from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from blog.models import (
    About,
    Conversation,
    Message,
    Partenaire,
    Presentation,
    Slide,
    Sponsor,
)

# Register your models here.


@admin.register(Slide)
class SlideAdmin(ImportExportModelAdmin):
    list_display = ("titre", "archive")
    search_fields = ("titre",)
    list_filter = ("titre",)


@admin.register(Sponsor)
class SponsorAdmin(ImportExportModelAdmin):
    list_display = ("nom", "logo", "archive")
    search_fields = ("nom",)
    list_filter = ("nom",)


@admin.register(Presentation)
class PresentationAdmin(ImportExportModelAdmin):
    list_display = ("titre", "phone1", "phone2", "email", "archive")
    search_fields = ("titre",)
    list_filter = ("titre",)


@admin.register(Partenaire)
class PartenaireAdmin(ImportExportModelAdmin):
    list_display = ("nom", "logo", "archive")
    search_fields = ("nom",)
    list_filter = ("nom",)


@admin.register(About)
class AboutAdmin(ImportExportModelAdmin):
    list_display = ("title", "picture", "archive")
    search_fields = ("title",)
    list_filter = ("title", "createdat")
    ordering = ("-createdat",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("announcement", "buyer", "seller", "started_at", "archive")
    search_fields = ("announcement",)
    list_filter = ("archive", "started_at")
    ordering = ("-createdat",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "sent_at", "is_read", "archive")
    search_fields = ("conversation",)
    list_filter = ("archive", "createdat")
