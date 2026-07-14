"""
API REST auth pour Next.js frontend.
Endpoints :
  POST /api/auth/register/ — inscription
  GET  /api/me/            — profil user connecte
  GET  /api/me/announcements/ — mes annonces
  GET  /api/me/ratings/    — mes avis recus
"""

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, serializers, status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SellerRating, SupportMessage, Utilisateur


class RegisterRateThrottle(AnonRateThrottle):
    """Limite stricte anti-abus sur l'inscription (scope 'register')."""

    scope = "register"


# ============================================================
# SERIALIZERS
# ============================================================


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(
        choices=Utilisateur.UserType.choices, required=False, default="individu"
    )

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telephone",
            "pays",
            "ville",
            "user_type",
            "password",
            "password_confirm",
        ]
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Les mots de passe ne correspondent pas."}
            )
        try:
            validate_password(attrs["password"])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        # Email unique
        email = attrs.get("email")
        if email and Utilisateur.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "Un compte existe deja avec cet email."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = Utilisateur(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MeSerializer(serializers.ModelSerializer):
    """Profil utilisateur complet pour le dashboard."""

    country_code = serializers.SerializerMethodField()
    country_name = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    rating_avg = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    transactions_count = serializers.SerializerMethodField()
    years_active = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telephone",
            "ville",
            "user_type",
            "date_joined",
            "country_code",
            "country_name",
            "picture_url",
            "display_name",
            "rating_avg",
            "ratings_count",
            "transactions_count",
            "years_active",
        ]
        read_only_fields = ["id", "date_joined"]

    def get_country_code(self, obj):
        return obj.pays.code if obj.pays else None

    def get_country_name(self, obj):
        return obj.pays.name if obj.pays else None

    def get_picture_url(self, obj):
        if obj.picture:
            request = self.context.get("request")
            url = obj.picture.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_rating_avg(self, obj):
        return obj.rating_avg

    def get_ratings_count(self, obj):
        return obj.ratings_count

    def get_transactions_count(self, obj):
        return obj.transactions_count

    def get_years_active(self, obj):
        return obj.years_active

    def get_display_name(self, obj):
        if obj.user_type == "entreprise":
            soc = getattr(obj, "societe", None)
            if soc:
                return soc.nom
        full = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full or obj.username


class RatingSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    author_country = serializers.SerializerMethodField()

    class Meta:
        model = SellerRating
        fields = [
            "id",
            "stars",
            "comment",
            "would_recommend",
            "created_at",
            "author_name",
            "author_country",
        ]

    def get_author_name(self, obj):
        if not obj.author:
            return "Anonyme"
        full = f"{obj.author.first_name or ''} {obj.author.last_name or ''}".strip()
        return full or obj.author.username

    def get_author_country(self, obj):
        if obj.author and obj.author.pays:
            return obj.author.pays.code
        return None


# ============================================================
# ENDPOINTS
# ============================================================


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([RegisterRateThrottle])
def register(request):
    """
    POST /api/auth/register/
    Inscription : cree un compte INACTIF et envoie un email de verification.
    L'utilisateur doit activer son compte avant de pouvoir se connecter.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )
    user = serializer.save()
    user.is_active = False
    user.save(update_fields=["is_active"])

    _send_activation_email(user)

    return Response(
        {
            "detail": (
                "Compte créé. Un email de vérification vient de vous être envoyé "
                "— cliquez sur le lien pour activer votre compte, puis connectez-vous."
            ),
            "email": user.email,
        },
        status=status.HTTP_201_CREATED,
    )


def _send_activation_email(user):
    """Envoie l'email d'activation avec un lien vers le frontend."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    front = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
    link = f"{front}/activate/{uid}/{token}"
    send_mail(
        subject="Activez votre compte — Agri Market Africa",
        message=(
            f"Bonjour {user.username},\n\n"
            f"Merci de votre inscription sur Agri Market Africa.\n"
            f"Activez votre compte en cliquant sur ce lien :\n\n{link}\n\n"
            f"Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n\n"
            f"L'équipe Agri Market Africa"
        ),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=True,
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def activate_account(request):
    """
    POST /api/auth/activate/  { "uid": "...", "token": "..." }
    Active le compte si le lien de vérification est valide.
    """
    uidb64 = request.data.get("uid")
    token = request.data.get("token")
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilisateur.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        return Response({"detail": "Compte activé. Vous pouvez vous connecter."})
    return Response(
        {"detail": "Lien d'activation invalide ou expiré."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    """
    GET  /api/me/   — profil de l'utilisateur connecte
    PATCH /api/me/  — mise a jour profil (partial)
    """
    user = request.user

    if request.method == "PATCH":
        allowed_fields = {
            "first_name",
            "last_name",
            "telephone",
            "ville",
            "pays",
        }
        for field, value in request.data.items():
            if field in allowed_fields:
                setattr(user, field, value)
        try:
            user.full_clean(
                exclude=["password", "date_joined", "last_login"]
            )
        except ValidationError as e:
            return Response(
                {"errors": e.message_dict}, status=status.HTTP_400_BAD_REQUEST
            )
        user.save()

    return Response(MeSerializer(user, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_announcements(request):
    """
    GET /api/me/announcements/
    Liste des annonces de l'utilisateur connecte, groupees par statut.
    """
    from marketplace.api import AnnouncementListSerializer
    from marketplace.models import Announcement

    qs = Announcement.objects.filter(user=request.user).select_related(
        "category", "subcategory"
    )

    def slice_by(status_val):
        return AnnouncementListSerializer(
            qs.filter(status=status_val).order_by("-publication_date")[:50],
            many=True,
            context={"request": request},
        ).data

    return Response(
        {
            "draft": slice_by("draft"),
            "pending_first": slice_by("pending_first"),
            "pending_second": slice_by("pending_second"),
            "approved": slice_by("approved"),
            "rejected": slice_by("rejected"),
            "expired": slice_by("expired"),
            "counts": {
                "draft": qs.filter(status="draft").count(),
                "pending": qs.filter(
                    Q(status="pending_first") | Q(status="pending_second")
                ).count(),
                "approved": qs.filter(status="approved").count(),
                "rejected": qs.filter(status="rejected").count(),
                "total": qs.count(),
            },
        }
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_ratings(request):
    """
    GET /api/me/ratings/
    Notes recues par l'utilisateur.
    """
    ratings = SellerRating.objects.filter(seller=request.user).select_related(
        "author"
    )[:100]
    return Response(
        {
            "summary": {
                "avg": request.user.rating_avg,
                "count": request.user.ratings_count,
            },
            "results": RatingSerializer(ratings, many=True).data,
        }
    )


# ============================================================
# MESSAGERIE SERVICE CLIENT
# ============================================================


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def support_messages(request):
    """
    GET  /api/support/messages/  -> fil de messagerie service client
    POST /api/support/messages/  { "body": "..." } -> envoyer un message
    """
    if request.method == "POST":
        body = (request.data.get("body") or "").strip()
        if not body:
            return Response(
                {"detail": "Message vide."}, status=status.HTTP_400_BAD_REQUEST
            )
        SupportMessage.objects.create(
            user=request.user, body=body[:4000], from_staff=False
        )

    # Les réponses du service client sont marquées comme lues à la consultation.
    SupportMessage.objects.filter(
        user=request.user, from_staff=True, is_read=False
    ).update(is_read=True)

    msgs = SupportMessage.objects.filter(user=request.user)
    return Response(
        {
            "messages": [
                {
                    "id": m.id,
                    "body": m.body,
                    "from_staff": m.from_staff,
                    "created_at": m.created_at.isoformat(),
                }
                for m in msgs
            ]
        }
    )
