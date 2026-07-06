import logging
import uuid

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from PIL import Image, UnidentifiedImageError
from taggit.managers import TaggableManager

from accounts.models import AFRICAN_COUNTRY_CODES, Utilisateur

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    """Classe de base abstraite pour les champs communs"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        abstract = True


class SubCategory(BaseModel):
    name = models.CharField(_("Nom"), max_length=100)

    class Meta:
        verbose_name = _("Sous-catégorie")
        verbose_name_plural = _("Sous-catégories")
        ordering = ["id"]

    def __str__(self):
        return self.name


class Category(BaseModel):
    name = models.CharField(_("Nom"), max_length=100)
    subcategories = models.ManyToManyField(
        SubCategory, verbose_name=_("Sous-catégories"), blank=True
    )

    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")
        ordering = ["id"]

    def __str__(self):
        return self.name


class AnnouncementType(models.TextChoices):
    SALE = "vente", _("Vente")
    PURCHASE = "achat", _("Achat")
    OTHER = "autre", _("Autre")


def generate_reference():
    return f"REF-{uuid.uuid4().hex[:10].upper()}"


class Announcement(BaseModel):
    STATUS_CHOICES = [
        ("draft", _("Brouillon")),
        ("pending_first", _("En attente première validation")),
        ("pending_second", _("En attente seconde validation")),
        ("approved", _("Approuvé")),
        ("rejected", _("Rejeté")),
        ("expired", _("Expiré")),
    ]

    # Référence avec préfixe REF-
    reference = models.CharField(
        _("Référence"),
        max_length=15,
        unique=True,
        editable=False,
        default=generate_reference,
    )
    product_name = models.CharField(
        _("Nom du produit"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Nom complet du produit (requis pour vente/achat)"),
    )
    title = models.CharField(_("Titre"), max_length=100)
    description = models.TextField(_("Description"), default="Description")
    caracteristiques = models.TextField(
        _("Les caractéristiques ou spécifications techniques des produits"),
        default="Caractéristiques ou spécifications",
        blank=True,
        null=True,
    )
    image = models.ImageField(
        _("Image"),
        upload_to="announcements/%Y/%m/",
        blank=True,
        null=True,
        help_text=_(
            "Image illustrative (optionnelle) les dimenssion de l'image doivent être lon:740 px et hau:380 px"
        ),
        default="announcements/default-product.jpg",
    )

    user = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        verbose_name=_("Utilisateur"),
        related_name="announcements",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name=_("Catégorie"),
    )

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        verbose_name=_("Sous-catégorie"),
        related_name="announcements",
    )

    type = models.CharField(
        max_length=20,
        choices=AnnouncementType.choices,
        default=AnnouncementType.SALE,
        verbose_name=_("Type d'annonce"),
    )

    brand = models.CharField(_("Marque"), max_length=100, blank=True)
    variety = models.CharField(_("Variété"), max_length=100, blank=True)
    quantity = models.PositiveIntegerField(
        _("Quantité"),
        null=True,
        blank=True,
        help_text=_("Quantité disponible ou requise"),
    )
    unit = models.CharField(
        _("Unité de mesure"),
        max_length=20,
        blank=True,
        help_text=_("kg, litre, pièce, etc."),
    )
    is_organic = models.BooleanField(_("Agriculture biologique"), default=False)

    country = CountryField(
        verbose_name=_("Pays"), blank=True, help_text=_("Pays concerné par l'annonce")
    )

    shipping_conditions = models.CharField(
        _("Conditions d'expédition"), max_length=100, blank=True
    )

    transaction_details = models.CharField(
        _("Détails de transaction"), max_length=100, blank=True
    )

    restrictions = models.CharField(_("Restrictions"), max_length=100, blank=True)

    tags = TaggableManager(
        _("Mots-clés"), blank=True, help_text=_("Mots-clés séparés par des virgules")
    )

    publication_date = models.DateTimeField(
        _("Date de publication"), blank=True, null=True, auto_now_add=True
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name=_("Statut")
    )

    first_approver = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="first_approved_announcements",
        verbose_name=_("Premier validateur"),
    )
    first_approval_date = models.DateTimeField(
        _("Date de première validation"), null=True, blank=True
    )
    second_approver = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="second_approved_announcements",
        verbose_name=_("Second validateur"),
    )
    second_approval_date = models.DateTimeField(
        _("Date de seconde validation"), null=True, blank=True
    )
    rejection_reason = models.TextField(_("Raison du rejet"), blank=True, null=True)

    class Meta:
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")
        ordering = ["-publication_date"]
        indexes = [
            models.Index(fields=["status", "is_archived", "publication_date"]),
            models.Index(fields=["type", "country"]),
            models.Index(fields=["reference"]),
        ]

    def get_absolute_url(self):
        return reverse("marketplace:announcement_detail", args=[str(self.id)])

    @property
    def is_african(self):
        return self.country.code in AFRICAN_COUNTRY_CODES if self.country else False

    def clean(self):
        super().clean()

        # Validation pour les annonces de vente/achat
        if self.type in [AnnouncementType.SALE, AnnouncementType.PURCHASE]:
            if not self.product_name:
                raise ValidationError(
                    {
                        "product_name": _(
                            "Le nom du produit est requis pour ce type d'annonce"
                        )
                    }
                )
            if self.quantity is None:
                raise ValidationError(
                    {"quantity": _("La quantité est requise pour ce type d'annonce")}
                )
            if not self.unit:
                raise ValidationError(
                    {"unit": _("L'unité de mesure est requise pour ce type d'annonce")}
                )

        # Validation de la quantité si renseignée
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError(
                {"quantity": _("La quantité doit être positive si renseignée")}
            )

        # Validation de l'image seulement si elle est uploadée (pas l'image par défaut)
        if self.image and not self.image.name == "announcements/default-product.jpg":
            if self.image.size > 500 * 1024:  # 500KB
                raise ValidationError("L'image ne doit pas dépasser 500KB")
            try:
                img = Image.open(self.image)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail((800, 600))
            except Exception:
                raise ValidationError("Erreur lors du traitement de l'image")

    def save(self, *args, **kwargs):

        if not self.reference or not self.reference.startswith("REF-"):
            self.reference = f"REF-{uuid.uuid4().hex[:10].upper()}"

        if not self.country and self.user and self.user.pays:
            self.country = self.user.pays

        super().save(*args, **kwargs)

        if self.image and "default-product" not in self.image.name:
            img_path = self.image.path

            try:
                img = Image.open(img_path)

                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                img = img.resize((740, 380), Image.LANCZOS)

                img.save(img_path, quality=90)

            except UnidentifiedImageError:
                pass

    @property
    def image_url(self):
        if self.image and hasattr(self.image, "url"):
            return self.image.url
        return f"{settings.MEDIA_URL}announcements/default-product.jpg"

    @property
    def get_status_badge(self):
        status_badges = {
            "draft": "secondary",
            "pending_first": "warning",
            "pending_second": "warning",
            "approved": "success",
            "rejected": "danger",
            "expired": "dark",
        }
        return status_badges.get(self.status, "secondary")

    def __str__(self):
        if self.title:
            type_display = self.get_type_display()
            return f"{self.reference} - {self.title} - {type_display}"
        return "Vue sans annonce"

    # Méthodes pour la validation
    def submit_for_approval(self):
        self.status = "pending_first"
        self.save()
        self._notify_validators("first")

    def approve_first(self, user):
        self.first_approver = user
        self.first_approval_date = timezone.now()
        self.status = "pending_second"
        self.save()
        self._notify_validators("second")

    def approve_second(self, user):
        self.second_approver = user
        self.second_approval_date = timezone.now()
        self.status = "approved"
        self.publication_date = timezone.now()
        self.save()
        self._notify_creator(_("Votre annonce a été approuvée"))

    def reject(self, user, reason):
        if self.status == "pending_first":
            self.first_approver = user
            self.first_approval_date = timezone.now()
        else:
            self.second_approver = user
            self.second_approval_date = timezone.now()

        self.rejection_reason = reason
        self.status = "rejected"
        self.save()
        self._notify_creator(_("Votre annonce a été rejetée"))

    def get_display_name(self):
        first_name = (self.user.first_name or "").strip()
        last_name = (self.user.last_name or "").strip()

        # Nettoyage des mauvaises valeurs
        if first_name.lower() == "none":
            first_name = ""
        if last_name.lower() == "none":
            last_name = ""

        full_name = f"{first_name} {last_name}".strip()

        return full_name if full_name else self.user.username

    def _notify_validators(self, stage):
        """Notifie les validateurs appropriés"""

        group_name = f"announcement_{stage}_validators"
        validators = Group.objects.get(name=group_name).user_set.all()

        current_site = Site.objects.get_current()
        domain = current_site.domain
        protocol = "https"

        for validator in validators:
            subject = _("Annonce en attente de validation")

            context = {
                "validator": validator,
                "announcement": self,
                "stage": stage,
                "domain": domain,
                "protocol": protocol,
            }

            message = render_to_string(
                "marketplace/emails/validation_notification.txt",
                context,
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [validator.email],
                fail_silently=True,
            )

    def _notify_creator(self, message):

        subject = _("Statut de votre annonce")

        # Nom utilisateur propre
        user_name = self.get_display_name()

        if not user_name:
            user_name = self.user.username

        # Domaine
        current_site = Site.objects.get_current()
        domain = current_site.domain

        context = {
            "user_name": user_name,
            "announcement": self,
            "message": message,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "domain": domain,
            "protocol": "https",  # ou "http" selon ton projet
        }

        send_mail(
            subject,
            render_to_string(
                "marketplace/emails/announcement_status_notification.txt", context
            ),
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
            fail_silently=True,
        )


class AnnouncementView(BaseModel):
    """Modèle pour suivre les vues des annonces"""

    announcement = models.ForeignKey(
        Announcement, on_delete=models.CASCADE, related_name="views"
    )
    user = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True
    )
    ip_address = models.CharField(max_length=40, blank=True)
    session_key = models.CharField(max_length=40, blank=True)

    class Meta:
        verbose_name = _("Vue d'annonce")
        verbose_name_plural = _("Vues d'annonces")
        constraints = [
            models.UniqueConstraint(
                fields=["announcement", "ip_address", "session_key"],
                name="unique_view_per_session",
            )
        ]

    def __str__(self):
        if self.announcement:
            type_display = self.announcement.get_type_display()
            return f"{self.announcement.reference} - {self.announcement.title} - {type_display}"
        return "Vue sans annonce"

    def save(self, *args, **kwargs):
        test_mode = kwargs.pop("test_mode", False)
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            if test_mode:
                raise
            pass


CRON_CHOICES = [
    ("validate_products", "Validate Products"),
    ("check_product_descriptions", "Check Product Descriptions"),
]


class CronTask(models.Model):
    name = models.CharField(max_length=50, choices=CRON_CHOICES, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({'Active' if self.active else 'Inactive'})"
