# marketplace/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import About, AboutPage, AboutValue, Presentation, Slide


@register(AboutPage)
class AboutPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "intro",
        "vision_title",
        "vision",
        "perspectives_title",
        "perspectives",
        "values_title",
        "mission_title",
        "mission",
    )


@register(AboutValue)
class AboutValueTranslationOptions(TranslationOptions):
    fields = ("title", "description")


@register(Slide)
class SlideTranslationOptions(TranslationOptions):
    fields = ("titre",)


@register(About)
class AboutTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Presentation)
class PresentationTranslationOptions(TranslationOptions):
    fields = ("titre",)
