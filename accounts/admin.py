from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from accounts.models import BlockedIP, Societe, Utilisateur

# Register your models here.


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    pass


@admin.register(Societe)
class SocieteAdmin(ImportExportModelAdmin):
    pass


@admin.register(Utilisateur)
class UtilisateurAdmin(ImportExportModelAdmin):
    pass
