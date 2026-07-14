"""
API REST pour la marketplace — consommee par Next.js frontend.
Endpoints : /api/announcements/, /api/categories/, /api/countries/counts/
"""

from django.conf import settings
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, serializers, viewsets
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Announcement, Category, SubCategory


# ============================================================
# SERIALIZERS
# ============================================================


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ["id", "name"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    annonces_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "subcategories", "annonces_count"]


class SellerLiteSerializer(serializers.Serializer):
    """Vendeur minimal (sans PII) pour la carte annonce."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.SerializerMethodField()
    country_code = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    rating_avg = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()

    def get_display_name(self, obj):
        if getattr(obj, "user_type", None) == "entreprise":
            soc = getattr(obj, "societe", None)
            if soc:
                return soc.nom
        full = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full or obj.username

    def get_country_code(self, obj):
        return obj.pays.code if obj.pays else None

    def get_country_name(self, obj):
        return obj.pays.name if obj.pays else None

    def get_picture(self, obj):
        if obj.picture:
            request = self.context.get("request")
            url = obj.picture.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_rating_avg(self, obj):
        return obj.rating_avg

    def get_ratings_count(self, obj):
        return obj.ratings_count


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Version list — legere, pour les grilles / rails."""

    seller = SellerLiteSerializer(source="user", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    subcategory_name = serializers.CharField(source="subcategory.name", read_only=True)
    image_url = serializers.SerializerMethodField()
    country_code = serializers.CharField(source="country.code", read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    published_at = serializers.DateTimeField(
        source="publication_date", read_only=True
    )

    class Meta:
        model = Announcement
        fields = [
            "id",
            "reference",
            "title",
            "type",
            "type_display",
            "is_organic",
            "quantity",
            "unit",
            "country_code",
            "country_name",
            "category_name",
            "subcategory_name",
            "seller",
            "image_url",
            "published_at",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        try:
            if obj.image and hasattr(obj.image, "url"):
                url = obj.image.url
                return request.build_absolute_uri(url) if request else url
        except Exception:
            pass
        return None


class AnnouncementDetailSerializer(AnnouncementListSerializer):
    """Version detail complete — pour la page produit."""

    description = serializers.CharField(read_only=True)
    caracteristiques = serializers.CharField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    variety = serializers.CharField(read_only=True)
    brand = serializers.CharField(read_only=True)
    shipping_conditions = serializers.CharField(read_only=True)
    transaction_details = serializers.CharField(read_only=True)

    class Meta(AnnouncementListSerializer.Meta):
        fields = AnnouncementListSerializer.Meta.fields + [
            "description",
            "caracteristiques",
            "product_name",
            "variety",
            "brand",
            "shipping_conditions",
            "transaction_details",
        ]


# ============================================================
# VIEWSETS
# ============================================================


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/announcements/       — liste (avec filtres)
    GET /api/announcements/{id}/  — detail
    Filters : ?q= &type= &category= &country= &bio=1 &sort=recent|popular|old
    """

    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description", "reference"]

    def get_queryset(self):
        qs = (
            Announcement.objects.filter(
                status="approved", is_archived=False
            )
            .select_related("user", "category", "subcategory")
            .prefetch_related("tags")
        )

        params = self.request.query_params

        q = params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(reference__icontains=q)
            )

        type_param = params.get("type")
        if type_param:
            qs = qs.filter(type=type_param)

        cat = params.get("category")
        if cat and cat.isdigit():
            qs = qs.filter(category_id=int(cat))

        country = params.get("country")
        if country:
            qs = qs.filter(country=country)

        if params.get("bio") == "1":
            qs = qs.filter(is_organic=True)

        sort = params.get("sort", "recent")
        if sort == "popular":
            qs = qs.annotate(views_count=Count("views")).order_by(
                "-views_count", "-publication_date"
            )
        elif sort == "old":
            qs = qs.order_by("publication_date")
        else:
            qs = qs.order_by("-publication_date")

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AnnouncementDetailSerializer
        return AnnouncementListSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/categories/ — liste avec compteur annonces
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return (
            Category.objects.filter(is_archived=False)
            .prefetch_related("subcategories")
            .annotate(
                annonces_count=Count(
                    "announcement",
                    filter=Q(
                        announcement__status="approved",
                        announcement__is_archived=False,
                    ),
                )
            )
            .order_by("-annonces_count", "name")
        )


# ============================================================
# ENDPOINTS "META" (stats globales)
# ============================================================


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def stats_summary(request):
    """
    GET /api/stats/summary/
    Stats globales pour le hero de la home.
    """
    from accounts.models import Utilisateur

    approved = Announcement.objects.filter(status="approved", is_archived=False)
    return Response(
        {
            "producteurs": Utilisateur.objects.count(),
            "pays_africains": 54,  # positionnement
            "filieres": SubCategory.objects.filter(is_archived=False).count(),
            "commission": "0%",
            "annonces_actives": approved.count(),
            "pays_actifs": approved.exclude(country="")
            .values("country")
            .distinct()
            .count(),
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def producer_of_month(request):
    """
    GET /api/producer-of-month/
    Utilisateur avec le + d'annonces approuvees + son annonce phare.
    """
    from accounts.models import Utilisateur

    top = (
        Utilisateur.objects.annotate(
            n_active=Count(
                "announcements",
                filter=Q(
                    announcements__status="approved",
                    announcements__is_archived=False,
                ),
            )
        )
        .filter(n_active__gt=0)
        .order_by("-n_active", "-date_joined")
        .first()
    )
    if not top:
        return Response({"producer": None, "featured": None})

    featured = (
        Announcement.objects.filter(
            user=top, status="approved", is_archived=False
        )
        .exclude(image="")
        .order_by("-publication_date")
        .first()
    )

    producer_data = SellerLiteSerializer(top, context={"request": request}).data
    producer_data.update(
        {
            "user_type": top.user_type,
            "years_active": top.years_active,
            "transactions_count": top.transactions_count,
            "trust_badges_count": len(top.trust_badges),
            "city": top.ville,
        }
    )
    featured_data = (
        AnnouncementListSerializer(
            featured, context={"request": request}
        ).data
        if featured
        else None
    )
    return Response({"producer": producer_data, "featured": featured_data})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def spotlight_category(request):
    """
    GET /api/spotlight-category/
    Categorie la plus active + son image cover + top 6 sous-filieres.
    """
    top_cat = (
        Category.objects.filter(is_archived=False)
        .annotate(
            annonces_count=Count(
                "announcement",
                filter=Q(
                    announcement__status="approved",
                    announcement__is_archived=False,
                ),
            )
        )
        .filter(annonces_count__gt=0)
        .prefetch_related("subcategories")
        .order_by("-annonces_count", "name")
        .first()
    )
    if not top_cat:
        return Response(None)

    # Cover : 1ere annonce approuvee avec image
    cover_ann = (
        Announcement.objects.filter(
            category=top_cat, status="approved", is_archived=False
        )
        .exclude(image="")
        .first()
    )
    cover_url = None
    if cover_ann and cover_ann.image:
        try:
            cover_url = request.build_absolute_uri(cover_ann.image.url)
        except Exception:
            pass

    return Response(
        {
            "id": top_cat.id,
            "name": top_cat.name,
            "annonces_count": top_cat.annonces_count,
            "cover_image": cover_url,
            "subcategories": [
                {"id": s.id, "name": s.name}
                for s in top_cat.subcategories.all()[:6]
            ],
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def countries_activity(request):
    """
    GET /api/countries/activity/
    Nombre d'annonces actives par pays (pour la carte d'Afrique).

    Reponse :
      {
        "total": 13,
        "counts": {"TG": 1, ...},                       # compat retro
        "countries": [{"code": "TG", "name": "Togo", "count": 1}, ...]
      }
    """
    from django_countries import countries as dj_countries

    counts_qs = (
        Announcement.objects.filter(status="approved", is_archived=False)
        .exclude(country="")
        .values("country")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    counts = {c["country"]: c["n"] for c in counts_qs}
    countries = [
        {
            "code": code,
            "name": dj_countries.name(code) or code,
            "count": n,
        }
        for code, n in counts.items()
    ]
    return Response(
        {
            "total": sum(counts.values()),
            "counts": counts,
            "countries": countries,
        }
    )


# ============================================================
# CREATION D'ANNONCE (utilisateur connecte)
# ============================================================


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """Serializer d'ecriture pour publier une annonce."""

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "type",
            "category",
            "subcategory",
            "product_name",
            "variety",
            "brand",
            "quantity",
            "unit",
            "is_organic",
            "country",
            "description",
            "caracteristiques",
            "shipping_conditions",
            "transaction_details",
            "image",
        ]

    def validate(self, attrs):
        t = attrs.get("type")
        if t in ("vente", "achat"):
            for field in ("product_name", "quantity", "unit"):
                if not attrs.get(field):
                    raise serializers.ValidationError(
                        {field: "Requis pour une annonce de vente/achat."}
                    )
        return attrs


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_announcement(request):
    """
    POST /api/me/announcements/create/
    Publie une annonce (utilisateur connecte). L'annonce entre dans le
    circuit de validation (statut 'pending_first').
    """
    serializer = AnnouncementCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=400)
    # AUTO_APPROVE_ANNOUNCEMENTS=True (staging) -> annonce visible tout de suite.
    # Sinon -> circuit de validation humaine ('pending_first').
    auto = getattr(settings, "AUTO_APPROVE_ANNOUNCEMENTS", False)
    ann = serializer.save(
        user=request.user,
        status="approved" if auto else "pending_first",
    )
    return Response(
        {
            "id": ann.id,
            "reference": ann.reference,
            "status": ann.status,
            "title": ann.title,
        },
        status=201,
    )


# ============================================================
# MESSAGERIE ACHETEUR <-> VENDEUR (par annonce)
# ============================================================


def _other_party(convo, me):
    other = convo.seller if convo.buyer_id == me.id else convo.buyer
    full = f"{other.first_name or ''} {other.last_name or ''}".strip()
    return {"id": other.id, "name": full or other.username}


def _convo_payload(convo, me):
    from blog.models import Message

    msgs = convo.messages.filter(deleted=False).select_related("sender")
    return {
        "conversation_id": convo.id,
        "with": _other_party(convo, me),
        "announcement": {
            "id": convo.announcement_id,
            "title": convo.announcement.title,
        },
        "messages": [
            {
                "id": m.id,
                "body": m.content or "",
                "mine": m.sender_id == me.id,
                "created_at": m.sent_at.isoformat(),
            }
            for m in msgs
        ],
    }


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def announcement_conversation(request, pk):
    """
    GET/POST /api/announcements/<pk>/messages/
    Ouvre (ou crée) la conversation acheteur<->vendeur pour l'annonce.
    """
    from blog.models import Conversation, Message

    ann = get_object_or_404(Announcement, pk=pk)
    me = request.user
    if ann.user_id == me.id:
        return Response(
            {"detail": "Vous êtes le vendeur de cette annonce."}, status=400
        )
    convo, _created = Conversation.objects.get_or_create(
        announcement=ann, buyer=me, seller=ann.user
    )
    if request.method == "POST":
        body = (request.data.get("body") or "").strip()
        if not body:
            return Response({"detail": "Message vide."}, status=400)
        Message.objects.create(conversation=convo, sender=me, content=body[:4000])
    Message.objects.filter(conversation=convo, is_read=False).exclude(
        sender=me
    ).update(is_read=True)
    return Response(_convo_payload(convo, me))


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def conversation_detail(request, pk):
    """GET/POST /api/conversations/<pk>/ — fil d'une conversation (participant)."""
    from blog.models import Conversation, Message

    convo = get_object_or_404(
        Conversation.objects.select_related("announcement", "buyer", "seller"),
        pk=pk,
    )
    me = request.user
    if me.id not in (convo.buyer_id, convo.seller_id):
        return Response({"detail": "Accès refusé."}, status=403)
    if request.method == "POST":
        body = (request.data.get("body") or "").strip()
        if not body:
            return Response({"detail": "Message vide."}, status=400)
        Message.objects.create(conversation=convo, sender=me, content=body[:4000])
    Message.objects.filter(conversation=convo, is_read=False).exclude(
        sender=me
    ).update(is_read=True)
    return Response(_convo_payload(convo, me))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_conversations(request):
    """GET /api/me/conversations/ — boîte de réception (acheteur + vendeur)."""
    from blog.models import Conversation

    me = request.user
    convos = (
        Conversation.objects.filter(Q(buyer=me) | Q(seller=me), archive=False)
        .select_related("announcement", "buyer", "seller")
        .order_by("-started_at")
    )
    out = []
    for c in convos:
        last = c.messages.filter(deleted=False).order_by("-sent_at").first()
        unread = c.messages.filter(is_read=False).exclude(sender=me).count()
        out.append(
            {
                "id": c.id,
                "with": _other_party(c, me),
                "announcement": {
                    "id": c.announcement_id,
                    "title": c.announcement.title,
                },
                "last": (last.content[:80] if last and last.content else ""),
                "unread": unread,
            }
        )
    return Response({"conversations": out})


