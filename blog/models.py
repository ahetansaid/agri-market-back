from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from accounts.models import Utilisateur
from idamarketplace.security import validate_document_upload, validate_image_upload
from marketplace.models import Announcement

# Create your models here.


class About(models.Model):
    title = models.CharField(_("Titre"), max_length=100, blank=True, null=True)
    description_fr = CKEditor5Field("Contenu en français", config_name="default")
    description_en = CKEditor5Field("Contenu en anglais", blank=True, null=True)
    description_it = CKEditor5Field("Contenu en italien", blank=True, null=True)
    picture = models.ImageField(
        _("picture"), upload_to="media/about", null=True, blank=True
    )
    archive = models.BooleanField(_("archive "), default=True, blank=True, null=True)
    createdat = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = _("À Propos")
        verbose_name_plural = _("À Propos de nous")

    def __str__(self):
        return f"{self.title}"


class Conversation(models.Model):
    announcement = models.ForeignKey(
        Announcement, on_delete=models.CASCADE, related_name="conversations", default=1
    )
    buyer = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="conversations_as_buyer",
        default=1,
    )
    seller = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="conversations_as_seller",
        default=2,
    )
    archive = models.BooleanField(_("archive "), default=False, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    createdat = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        unique_together = (
            "announcement",
            "buyer",
            "seller",
        )  # Une seule conversation par annonce/buyer/seller

    def __str__(self):
        return (
            f"Conversation sur {self.announcement} entre {self.buyer} et {self.seller}"
        )


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    attachment = models.FileField(
        upload_to="messages/files/",
        blank=True,
        null=True,
        validators=[validate_document_upload],
    )

    image = models.ImageField(
        upload_to="messages/images/",
        blank=True,
        null=True,
        validators=[validate_image_upload],
    )

    archive = models.BooleanField(_("archive "), default=False, blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    createdat = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ["sent_at"]

    def __str__(self):
        return f"Message de {self.sender} à {self.sent_at}"

    def clean(self):

        if not self.content and not self.attachment and not self.image:
            raise ValidationError("Un message doit contenir du texte ou un fichier.")


class Partenaire(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du partenaire")
    logo = models.ImageField(upload_to="media/partenaires/", verbose_name="Logo")
    archive = models.BooleanField(_("archive "), default=False, blank=True, null=True)
    createdat = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Sponsor(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du Sponsor")
    logo = models.ImageField(upload_to="media/Sponsor/", verbose_name="Logo")
    archive = models.BooleanField(
        _("archive Sponsor "), default=False, blank=True, null=True
    )
    createdat = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = "Sponsor"
        verbose_name_plural = "Sponsors"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Presentation(models.Model):
    titre = models.CharField(
        max_length=255, verbose_name="Nom de l'ONG", blank=True, null=True
    )
    phone1 = models.CharField(
        max_length=255, verbose_name="Téléphone 1", blank=True, null=True
    )
    phone2 = models.CharField(
        max_length=255, verbose_name="Téléphone 2", blank=True, null=True
    )
    email = models.EmailField(_("Email"), max_length=254, blank=True, null=True)
    description_fr = CKEditor5Field("Contenu en français", config_name="default")
    description_en = CKEditor5Field("Contenu en anglais", blank=True, null=True)
    description_it = CKEditor5Field("Contenu en italien", blank=True, null=True)
    image = models.ImageField(upload_to="media/presentation/", verbose_name="image")
    logo = models.ImageField(upload_to="media/presentation/", verbose_name="Logo")
    archive = models.BooleanField(_("archive "), default=False, blank=True, null=True)
    createdat = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updateDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = "Presentation"
        verbose_name_plural = "Presentations"
        ordering = ["titre"]

    def __str__(self):
        return self.titre


class Slide(models.Model):
    titre = models.CharField(_("Titre"), max_length=200, blank=True, null=True)
    description_fr = CKEditor5Field(
        "Contenu en français", config_name="default", blank=True, null=True
    )
    description_en = CKEditor5Field("Contenu en anglais", blank=True, null=True)
    description_it = CKEditor5Field("Contenu en italien", blank=True, null=True)
    image_fr = models.ImageField(
        _("Image (FR)"), upload_to="media/slide/", blank=True, null=True
    )
    image_en = models.ImageField(
        _("Image (EN)"), upload_to="media/slide/", blank=True, null=True
    )
    image_it = models.ImageField(
        _("Image (IT)"), upload_to="media/slide/", blank=True, null=True
    )
    archive = models.BooleanField(_("archive "), default=True, blank=True, null=True)
    url = models.CharField(_("Ulr"), max_length=200, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        ordering = ["titre"]

    def __str__(self):
        return self.titre

    def get_image_by_lang(self, lang_code):
        """Retourne l’image selon la langue choisie"""
        if lang_code == "fr" and self.image_fr:
            return self.image_fr.url
        elif lang_code == "en" and self.image_en:
            return self.image_en.url
        elif lang_code == "it" and self.image_it:
            return self.image_it.url
        # Fallback → retourne FR par défaut ou None
        return self.image_fr.url if self.image_fr else None
