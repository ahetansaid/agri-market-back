from django.contrib import admin
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

from .cron_control import update_crontabs
from .models import Announcement, AnnouncementView, Category, CronTask, SubCategory


@admin.register(AnnouncementView)
class AnnouncementViewAdmin(admin.ModelAdmin):
    list_display = ("announcement", "user", "ip_address", "session_key", "created_at")
    search_fields = ("announcement__title", "user__username", "ip_address")
    list_filter = ("announcement__type",)


@admin.register(SubCategory)
class SubCategoryAdmin(ImportExportModelAdmin):
    list_display = ("name", "announcement_count", "is_archived", "created_at")
    search_fields = ("name",)
    list_filter = ("is_archived", "created_at")
    ordering = ("-created_at",)

    @admin.display(description=_("Nb annonces"))
    def announcement_count(self, obj):
        return obj.announcements.count()


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ("name", "subcategories_count", "is_archived", "created_at")
    search_fields = ("name",)
    list_filter = ("is_archived",)
    filter_horizontal = ("subcategories",)
    ordering = ("-created_at",)

    @admin.display(description=_("Nb sous-catégories"))
    def subcategories_count(self, obj):
        return obj.subcategories.count()


@admin.register(Announcement)
class AnnouncementAdmin(ImportExportModelAdmin):
    list_display = (
        "reference",
        "title",
        "user",
        "type",
        "quantity_display",
        "country",
        "view_count",
        "status",
        "created_at",
        "image_preview",
        "is_archived",
    )
    search_fields = (
        "title",
        "user__username",
        "description",
        "tags__name",
        "reference",
    )
    list_filter = (
        "type",
        "country",
        "status",
        "category",
        "subcategory",
        "is_organic",
        "is_archived",
    )
    ordering = ("-created_at",)
    readonly_fields = ("reference", "image_preview", "created_at", "updated_at")
    raw_id_fields = ("user",)
    list_select_related = ("user", "category", "subcategory")
    actions = ["mark_as_approved", "mark_as_rejected", "archive", "unarchive"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "reference",
                    "title",
                    "title_fr",
                    "title_en",
                    "title_it",
                    "description",
                    "description_fr",
                    "description_en",
                    "description_it",
                    "caracteristiques",
                    "caracteristiques_fr",
                    "caracteristiques_en",
                    "caracteristiques_it",
                    "brand",
                    "brand_fr",
                    "brand_en",
                    "brand_it",
                    "variety",
                    "variety_fr",
                    "variety_en",
                    "variety_it",
                    "unit",
                    "unit_fr",
                    "unit_en",
                    "unit_it",
                    "shipping_conditions",
                    "shipping_conditions_fr",
                    "shipping_conditions_en",
                    "shipping_conditions_it",
                    "transaction_details",
                    "transaction_details_fr",
                    "transaction_details_en",
                    "transaction_details_it",
                    "restrictions",
                    "restrictions_fr",
                    "restrictions_en",
                    "restrictions_it",
                    "user",
                    "type",
                    "status",
                    "is_archived",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            _("Contenu"),
            {
                "fields": (
                    "category",
                    "subcategory",
                    "product_name",
                    "tags",
                    "image",
                    "image_preview",
                )
            },
        ),
        (
            _("Détails"),
            {
                "fields": (
                    "quantity",
                    "is_organic",
                )
            },
        ),
        (
            _("Localisation & Logistique"),
            {"fields": ("country",)},
        ),
    )

    @admin.display(description=_("Quantité"))
    def quantity_display(self, obj):
        if obj.quantity:
            return f"{obj.quantity} {obj.unit}" if obj.unit else obj.quantity
        return "-"

    @admin.display(description=_("Nombre de vues"))
    def view_count(self, obj):
        """Retourne le nombre total de vues liées à l’annonce."""
        return obj.views.count()

    @admin.display(description=_("Aperçu image"))
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />'
            )
        return _("Aucune image")

    @admin.action(description=_("Marquer comme approuvé"))
    def mark_as_approved(self, request, queryset):
        annonces = list(queryset.select_related("user"))
        queryset.update(status="approved")
        self._notify_authors(
            annonces,
            "Votre annonce est en ligne",
            "a été validée et est désormais visible sur la marketplace.",
        )

    @admin.action(description=_("Marquer comme rejeté"))
    def mark_as_rejected(self, request, queryset):
        annonces = list(queryset.select_related("user"))
        queryset.update(status="rejected")
        self._notify_authors(
            annonces,
            "Votre annonce a été refusée",
            (
                "n'a pas été retenue. Vérifiez qu'elle ne contient aucune "
                "coordonnée personnelle (téléphone, email, site web) et qu'elle "
                "respecte les conditions d'utilisation, puis republiez-la."
            ),
        )

    @staticmethod
    def _notify_authors(annonces, title, sentence):
        """Prévient les auteurs (notification + email). Best-effort."""
        from accounts.api import notify

        for ann in annonces:
            notify(
                ann.user,
                title=title,
                body=f"« {ann.title} » (réf. {ann.reference}) {sentence}",
                kind="announcement",
                link="/dashboard/producer/announcements",
                email=True,
            )

    @admin.action(description=_("Archiver les annonces sélectionnées"))
    def archive(self, request, queryset):
        queryset.update(is_archived=True)

    @admin.action(description=_("Désarchiver les annonces sélectionnées"))
    def unarchive(self, request, queryset):
        queryset.update(is_archived=False)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags")


@admin.register(CronTask)
class CronTaskAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_editable = ("active",)

    @receiver(post_save, sender=CronTask)
    def update_cron_jobs(sender, instance, **kwargs):
        update_crontabs()
