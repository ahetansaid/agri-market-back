from django.conf import settings
from django_countries import countries

from marketplace.models import Category, SubCategory


def global_context(request):
    # Liste des pays africains avec noms complets
    african_countries = [
        (code, countries.name(code))
        for code in settings.AFRICAN_COUNTRY_CODES
        if code in countries.countries
    ]

    return {
        "african_countries": sorted(
            african_countries, key=lambda x: x[1]
        ),  # Tri par nom
        "SITE_NAME": "IDA Marketplace",
        # Ajoutez ici d'autres variables globales si nécessaire
        "is_first_validator": request.user.groups.filter(
            name="announcement_first_validators"
        ).exists(),
        "is_second_validator": request.user.groups.filter(
            name="announcement_second_validators"
        ).exists(),
    }


def mobilemenu_context(request):
    categories = Category.objects.prefetch_related("subcategories").filter(
        is_archived=False
    )
    sousbcategory = SubCategory.objects.filter(is_archived=False)
    user = request.user
    return {"categories": categories, "user": user, "sousbcategory": sousbcategory}
