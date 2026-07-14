from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from accounts.models import BlockedIP, Societe, SupportMessage, Utilisateur

# Register your models here.


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    pass


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    """Messagerie service client. Pour repondre : ajouter un message avec
    l'utilisateur concerne et 'Reponse du service client' coche."""

    list_display = ("user", "from_staff", "short_body", "is_read", "created_at")
    list_filter = ("from_staff", "is_read", "created_at")
    search_fields = ("user__username", "user__email", "body")
    raw_id_fields = ("user",)
    list_select_related = ("user",)

    @admin.display(description="Message")
    def short_body(self, obj):
        return (obj.body[:60] + "…") if len(obj.body) > 60 else obj.body


@admin.register(Societe)
class SocieteAdmin(ImportExportModelAdmin):
    pass


@admin.register(Utilisateur)
class UtilisateurAdmin(ImportExportModelAdmin):
    pass
