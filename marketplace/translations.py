# marketplace/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import Announcement, Category, SubCategory


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(SubCategory)
class SubCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Announcement)
class AnnouncementTranslationOptions(TranslationOptions):
    fields = (
        "title",
        # "product_name",
        "description",
        "caracteristiques",
        "brand",
        "variety",
        "unit",
        "shipping_conditions",
        "transaction_details",
        "restrictions",
    )
