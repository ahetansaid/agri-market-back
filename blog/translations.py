# marketplace/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import About, Presentation, Slide


@register(Slide)
class SlideTranslationOptions(TranslationOptions):
    fields = ("titre",)


@register(About)
class AboutTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Presentation)
class PresentationTranslationOptions(TranslationOptions):
    fields = ("titre",)
