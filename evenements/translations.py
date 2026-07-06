# marketplace/translation.py
from modeltranslation.translator import TranslationOptions, register

from .models import Evenement, Question, Questionnaire, SectionQuestionnaire


@register(Evenement)
class EvenementTranslationOptions(TranslationOptions):
    fields = ("titre",)


@register(Questionnaire)
class QuestionnaireTranslationOptions(TranslationOptions):
    fields = ("nom",)


@register(Question)
class QuestionTranslationOptions(TranslationOptions):
    fields = ("libelle", "aide_texte", "options")


@register(SectionQuestionnaire)
class SectionQuestionnaireTranslationOptions(TranslationOptions):
    fields = ("nom", "description")
