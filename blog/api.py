"""API REST de la page « À propos » — consommée par le frontend Next.js.

Le contenu est traduit automatiquement selon l'en-tête Accept-Language
(LocaleMiddleware + modeltranslation, fallback FR).
"""

from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import AboutPage, AboutValue

EDITABLE_FIELDS = [
    "title",
    "intro",
    "vision_title",
    "vision",
    "perspectives_title",
    "perspectives",
    "values_title",
    "mission_title",
    "mission",
]


class AboutValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutValue
        fields = ["icon", "title", "description"]


class AboutPageSerializer(serializers.ModelSerializer):
    values = AboutValueSerializer(many=True, read_only=True)

    class Meta:
        model = AboutPage
        fields = [
            "title",
            "intro",
            "vision_title",
            "vision",
            "perspectives_title",
            "perspectives",
            "values_title",
            "mission_title",
            "mission",
            "values",
        ]


@api_view(["GET"])
@permission_classes([AllowAny])
def about_page(request):
    """GET /api/about/ — contenu structuré de la page À propos (ou {} si vide)."""
    page = (
        AboutPage.objects.filter(is_active=True)
        .prefetch_related("values")
        .first()
    )
    if not page:
        return Response({})
    return Response(AboutPageSerializer(page).data)


# ============================================================
# ADMIN (staff-only) — édition de la page À propos
# ============================================================


def _serialize_editable(page):
    """Contenu éditable dans la LANGUE ACTIVE (modeltranslation) + ids des
    valeurs pour permettre la mise à jour côté admin."""
    data = {f: getattr(page, f) or "" for f in EDITABLE_FIELDS}
    data["values"] = [
        {
            "id": v.id,
            "icon": v.icon,
            "title": v.title or "",
            "description": v.description or "",
        }
        for v in page.values.all()
    ]
    return data


@api_view(["GET", "PUT"])
@permission_classes([IsAdminUser])
def admin_about(request):
    """GET/PUT /api/admin/about/ — édite la page À propos.

    L'écriture cible la langue active (en-tête Accept-Language + modeltranslation),
    donc le sélecteur de langue du front choisit quelle traduction est éditée.
    """
    page = AboutPage.objects.filter(is_active=True).first()
    if not page:
        page = AboutPage.objects.create(
            intro="", vision="", perspectives="", mission=""
        )

    if request.method == "GET":
        return Response(_serialize_editable(page))

    # PUT : mise à jour des champs texte (langue active) + synchro des valeurs.
    data = request.data
    for field in EDITABLE_FIELDS:
        if field in data:
            setattr(page, field, (data.get(field) or "").strip())
    page.save()

    incoming = data.get("values") or []
    kept_ids = []
    for order, v in enumerate(incoming):
        vid = v.get("id")
        val = None
        if vid:
            val = AboutValue.objects.filter(page=page, id=vid).first()
        if val is None:
            val = AboutValue(page=page)
        val.icon = (v.get("icon") or "Sparkles").strip()
        val.title = (v.get("title") or "").strip()
        val.description = (v.get("description") or "").strip()
        val.order = order
        val.save()
        kept_ids.append(val.id)
    # Supprime les valeurs retirées côté admin.
    AboutValue.objects.filter(page=page).exclude(id__in=kept_ids).delete()

    page.refresh_from_db()
    return Response(_serialize_editable(page))
