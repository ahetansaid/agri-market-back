from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

from .models import (
    Evenement,
    InteretEvenement,
    Question,
    Questionnaire,
    ReponseQuestion,
    SectionQuestion,
    SectionQuestionnaire,
)


class SectionQuestionInline(admin.TabularInline):
    model = SectionQuestion
    extra = 1
    ordering = ["ordre"]
    raw_id_fields = ["question"]


class SectionQuestionnaireAdmin(ImportExportModelAdmin):
    list_display = ["nom", "ordre", "get_questions_count"]
    inlines = [SectionQuestionInline]
    ordering = ["ordre"]

    @admin.display(description=_("Nombre de questions"))
    def get_questions_count(self, obj):
        return obj.questions.count()


class QuestionAdmin(ImportExportModelAdmin):
    list_display = [
        "libelle",
        "type_question",
        "obligatoire",
        "ordre",
        "get_options_preview",
    ]
    list_filter = ["type_question", "obligatoire"]
    search_fields = ["libelle"]
    list_editable = ["ordre"]

    @admin.display(description=_("Options (aperçu)"))
    def get_options_preview(self, obj):
        if obj.options:
            return obj.options[:50] + "..." if len(obj.options) > 50 else obj.options
        return "-"


class QuestionnaireAdmin(ImportExportModelAdmin):
    list_display = [
        "nom",
        "actif",
        "date_creation",
        "get_sections_count",
        "display_image_fr",
    ]
    filter_horizontal = ["sections"]
    list_filter = ["actif"]
    date_hierarchy = "date_creation"
    readonly_fields = ["display_image_fr"]

    @admin.display(description=_("Image"))
    def display_image_fr(self, obj):
        if obj.image_fr:
            return mark_safe(f'<img src="{obj.image_fr.url}" width="100" />')
        return "-"

    @admin.display(description=_("Nombre de sections"))
    def get_sections_count(self, obj):
        return obj.sections.count()


class ReponseQuestionInline(admin.TabularInline):
    model = ReponseQuestion
    extra = 0
    readonly_fields = ["question"]
    fields = ["question", "valeur", "fichier"]
    raw_id_fields = ["question"]


class InteretEvenementAdmin(ImportExportModelAdmin):
    list_display = [
        "nom_complet",
        "email",
        "evenement",
        "date_creation",
        "interesse",
        "accepte_newsletter",
    ]
    list_filter = ["evenement", "interesse", "accepte_newsletter"]
    search_fields = ["nom_complet", "email", "evenement__titre"]
    inlines = [ReponseQuestionInline]
    date_hierarchy = "date_creation"
    raw_id_fields = ["utilisateur", "evenement"]


class EvenementAdmin(ImportExportModelAdmin):
    list_display = [
        "titre",
        "date_debut",
        "date_fin",
        "est_actif",
        "questionnaire",
        "count_interesses",
    ]
    list_filter = ["est_actif", "questionnaire"]
    search_fields = [
        "titre",
    ]
    prepopulated_fields = {"slug": ["titre"]}
    raw_id_fields = ["questionnaire"]
    date_hierarchy = "date_debut"


admin.site.register(Question, QuestionAdmin)
admin.site.register(SectionQuestionnaire, SectionQuestionnaireAdmin)
admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(Evenement, EvenementAdmin)
admin.site.register(InteretEvenement, InteretEvenementAdmin)
