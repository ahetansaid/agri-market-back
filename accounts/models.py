from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

AFRICAN_COUNTRY_CODES = [
    "DZ",
    "AO",
    "BJ",
    "BW",
    "BF",
    "BI",
    "CM",
    "CV",
    "CF",
    "TD",
    "KM",
    "CG",
    "CD",
    "CI",
    "DJ",
    "EG",
    "GQ",
    "ER",
    "SZ",
    "ET",
    "GA",
    "GM",
    "GH",
    "GN",
    "GW",
    "KE",
    "LS",
    "LR",
    "LY",
    "MG",
    "MW",
    "ML",
    "MR",
    "MU",
    "YT",
    "MA",
    "MZ",
    "NA",
    "NE",
    "NG",
    "RW",
    "RE",
    "ST",
    "SN",
    "SC",
    "SL",
    "SO",
    "ZA",
    "SS",
    "SD",
    "TZ",
    "TG",
    "TN",
    "UG",
    "EH",
    "ZM",
    "ZW",
]


class Utilisateur(AbstractUser):
    ACCOUNT_EMAIL_REQUIRED = False

    class UserType(models.TextChoices):
        INDIVIDU = "individu", _("Individu")
        ENTREPRISE = "entreprise", _("Entreprise")

    # Champs communs
    email = models.EmailField(_("email address"), unique=True)
    telephone = PhoneNumberField(_("Téléphone"), region=None, blank=True, null=True)
    pays = CountryField(blank=True, null=True, verbose_name=_("Pays"))
    ville = models.CharField(_("Ville"), max_length=50, blank=True, null=True)
    code_postal = models.CharField(
        _("Code Postal"), max_length=20, blank=True, null=True
    )
    adresse = models.CharField(_("Adresse"), max_length=255, blank=True, null=True)
    picture = models.ImageField(
        _("Image de profil"), upload_to="user/", null=True, blank=True
    )

    user_type = models.CharField(
        _("Type d'utilisateur"),
        max_length=20,
        choices=UserType.choices,
        default=UserType.INDIVIDU,
    )

    # Champs spécifiques aux individus
    first_name = models.CharField(_("Prénom"), max_length=150, blank=True, null=True)
    last_name = models.CharField(_("Nom"), max_length=150, blank=True, null=True)

    class IndividualCategory(models.TextChoices):
        AGRICULTEUR = "agriculteur", _("Agriculteur")
        INVESTISSEUR = "investisseur", _("Investisseur")
        OPPORTUNISTE = "opportuniste", _("Chercheur d'opportunités")
        FOURNISSEUR = "fournisseur", _("Fournisseur de services")

    individual_category = models.CharField(
        _("Catégorie d'individu"),
        max_length=50,
        choices=IndividualCategory.choices,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

    def clean(self):
        super().clean()
        # Nettoyage conditionnel des champs selon le type d'utilisateur
        if self.user_type == self.UserType.ENTREPRISE:
            # Pour les entreprises, on nettoie les champs d'individu
            self.first_name = None
            self.last_name = None
            self.individual_category = None

        # Validation conditionnelle
        if self.user_type == self.UserType.INDIVIDU:
            if not self.individual_category:
                raise ValidationError(
                    {
                        "individual_category": _(
                            "Ce champ est obligatoire pour les individus"
                        )
                    }
                )

        # Validation pour les entreprises
        if self.user_type == self.UserType.ENTREPRISE:
            if self.individual_category:
                raise ValidationError(
                    {
                        "individual_category": _(
                            "Ce champ ne doit pas être renseigné pour les entreprises"
                        )
                    }
                )

    @property
    def is_african(self):
        return self.pays.code in AFRICAN_COUNTRY_CODES if self.pays else False

    @property
    def est_entreprise(self):
        return self.user_type == self.UserType.ENTREPRISE

    @property
    def est_individu(self):
        return self.user_type == self.UserType.INDIVIDU

    def __str__(self):
        return self.username


class Societe(models.Model):
    class CompanyType(models.TextChoices):
        PRODUCTEUR = "producteur", _("Producteur")
        DISTRIBUTEUR = "distributeur", _("Distributeur")
        REVENDEUR = "revendeur", _("Revendeur")
        AUTRE = "autre", _("Autre")

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="societe"
    )
    nom = models.CharField(_("Nom de la société"), max_length=255)
    company_type = models.CharField(
        _("Type d'entreprise"), max_length=50, choices=CompanyType.choices
    )
    autre_type = models.CharField(
        _("Précisez le type"), max_length=100, blank=True, null=True
    )
    code_commercial = models.CharField(
        _("Code du commercial"), max_length=50, blank=True, null=True
    )

    produits_vendus = models.ManyToManyField(
        "marketplace.Category",
        related_name="societes_vendeuses",
        verbose_name=_("Produits vendus"),
        blank=True,
    )
    produits_recherches = models.ManyToManyField(
        "marketplace.Category",
        related_name="societes_acheteuses",
        verbose_name=_("Produits recherchés"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Société")
        verbose_name_plural = _("Sociétés")

    def clean(self):
        super().clean()
        if self.company_type == self.CompanyType.AUTRE and not self.autre_type:
            raise ValidationError(
                {"autre_type": _("Veuillez préciser le type d'entreprise")}
            )

    def __str__(self):
        return self.nom


class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ip_address


# ============================================================
# REPUTATION SYSTEM — Made in Africa
# Notes vendeur + badges de confiance contexte africain
# ============================================================


class SellerRating(models.Model):
    """Note laissee par un acheteur a un vendeur apres transaction."""

    STARS_CHOICES = [(i, f"{i} ⭐") for i in range(1, 6)]

    seller = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="ratings_received",
        verbose_name=_("Vendeur"),
    )
    author = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ratings_given",
        verbose_name=_("Auteur"),
    )
    stars = models.PositiveSmallIntegerField(
        _("Étoiles"), choices=STARS_CHOICES, default=5
    )
    comment = models.TextField(_("Commentaire"), blank=True, max_length=800)
    would_recommend = models.BooleanField(_("Recommande"), default=True)
    announcement = models.ForeignKey(
        "marketplace.Announcement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratings",
        verbose_name=_("Annonce concernée"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Note vendeur")
        verbose_name_plural = _("Notes vendeurs")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["seller", "author", "announcement"],
                name="unique_rating_per_transaction",
            )
        ]

    def __str__(self):
        return f"{self.author} → {self.seller} : {self.stars}⭐"


# ---------- Properties reputation ajoutees a Utilisateur ----------

from django.db.models import Avg, Count  # noqa: E402


def _rating_avg(self):
    """Note moyenne sur 5. Retourne None si aucune note."""
    from datetime import timedelta
    from django.utils import timezone as _tz

    key = "_cached_rating_avg"
    if hasattr(self, key):
        return getattr(self, key)
    result = SellerRating.objects.filter(seller=self).aggregate(a=Avg("stars"))["a"]
    val = round(result, 1) if result else None
    setattr(self, key, val)
    return val


def _ratings_count(self):
    key = "_cached_ratings_count"
    if hasattr(self, key):
        return getattr(self, key)
    n = SellerRating.objects.filter(seller=self).count()
    setattr(self, key, n)
    return n


def _transactions_count(self):
    """Nombre d'annonces approuvees (proxy transactions/impact)."""
    from marketplace.models import Announcement

    key = "_cached_tx_count"
    if hasattr(self, key):
        return getattr(self, key)
    n = Announcement.objects.filter(user=self, status="approved").count()
    setattr(self, key, n)
    return n


def _years_active(self):
    from django.utils import timezone as _tz

    if not self.date_joined:
        return 0
    return max(0, _tz.now().year - self.date_joined.year)


def _trust_badges(self):
    """Liste de badges 'Made in Africa' selon activite et localisation.

    Retourne une liste de dicts : {slug, label, icon, tone}
    Tone : 'gold' | 'green' | 'orange' | 'blue' | 'terra'
    """
    badges = []

    # Coopérative agréée (utilisateur entreprise producteur)
    if getattr(self, "user_type", None) == "entreprise":
        soc = getattr(self, "societe", None)
        if soc and soc.company_type == "producteur":
            badges.append(
                {
                    "slug": "cooperative",
                    "label": _("Coopérative Agréée"),
                    "icon": "ti-users-group",
                    "tone": "green",
                }
            )
        elif soc:
            badges.append(
                {
                    "slug": "entreprise",
                    "label": _("Entreprise vérifiée"),
                    "icon": "ti-building",
                    "tone": "blue",
                }
            )

    # Africain (pays africain)
    try:
        if self.pays and self.pays.code in AFRICAN_COUNTRY_CODES:
            badges.append(
                {
                    "slug": "africa",
                    "label": _("Made in Africa"),
                    "icon": "ti-world",
                    "tone": "terra",
                }
            )
    except Exception:
        pass

    # Transactions
    tx = self.transactions_count
    if tx >= 10:
        badges.append(
            {
                "slug": "tx-10",
                "label": _("10+ transactions"),
                "icon": "ti-handshake",
                "tone": "gold",
            }
        )
    elif tx >= 3:
        badges.append(
            {
                "slug": "tx-3",
                "label": _("Vendeur actif"),
                "icon": "ti-check",
                "tone": "orange",
            }
        )

    # Note excellente
    avg = self.rating_avg
    if avg and avg >= 4.5:
        badges.append(
            {
                "slug": "top-rated",
                "label": _("Top noté"),
                "icon": "ti-star-filled",
                "tone": "gold",
            }
        )

    # Ancienneté
    years = self.years_active
    if years >= 3:
        badges.append(
            {
                "slug": "veteran",
                "label": _("Vétéran %(y)s ans") % {"y": years},
                "icon": "ti-award",
                "tone": "gold",
            }
        )
    elif years >= 1:
        badges.append(
            {
                "slug": "member",
                "label": _("Membre %(y)s an") % {"y": years}
                if years == 1
                else _("Membre %(y)s ans") % {"y": years},
                "icon": "ti-calendar-check",
                "tone": "orange",
            }
        )

    return badges


# Attache dynamiquement au modele Utilisateur (evite subclasse)
Utilisateur.rating_avg = property(_rating_avg)
Utilisateur.ratings_count = property(_ratings_count)
Utilisateur.transactions_count = property(_transactions_count)
Utilisateur.years_active = property(_years_active)
Utilisateur.trust_badges = property(_trust_badges)


# ============================================================
# MESSAGERIE SERVICE CLIENT (fil par utilisateur)
# ============================================================


class SupportMessage(models.Model):
    """Un message dans le fil de messagerie service client d'un utilisateur."""

    user = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="support_messages",
        verbose_name=_("Utilisateur"),
    )
    body = models.TextField(_("Message"))
    from_staff = models.BooleanField(_("Réponse du service client"), default=False)
    is_read = models.BooleanField(_("Lu par le destinataire"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Message support")
        verbose_name_plural = _("Messages support")
        ordering = ["created_at"]

    def __str__(self):
        who = "Service client" if self.from_staff else str(self.user)
        return f"{who} — {self.created_at:%d/%m %H:%M}"


class Notification(models.Model):
    """Notification destinée à un utilisateur (message, validation, retour…)."""

    class Kind(models.TextChoices):
        MESSAGE = "message", _("Message")
        ANNOUNCEMENT = "announcement", _("Annonce")
        REVIEW = "review", _("Avis")
        SYSTEM = "system", _("Système")

    user = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Destinataire"),
    )
    kind = models.CharField(
        _("Type"), max_length=20, choices=Kind.choices, default=Kind.SYSTEM
    )
    title = models.CharField(_("Titre"), max_length=200)
    body = models.TextField(_("Détail"), blank=True, default="")
    # Chemin côté frontend (ex: /messages/12, /dashboard/producer/announcements)
    link = models.CharField(_("Lien"), max_length=300, blank=True, default="")
    is_read = models.BooleanField(_("Lue"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user} — {self.title}"
