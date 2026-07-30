"""API REST de la page « À propos » — consommée par le frontend Next.js.

Le contenu est traduit automatiquement selon l'en-tête Accept-Language
(LocaleMiddleware + modeltranslation, fallback FR).
"""

from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import AboutPage, AboutValue


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
