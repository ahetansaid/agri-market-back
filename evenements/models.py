import uuid

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field


class QuestionType(models.TextChoices):
    TEXTE_COURT = "TC", _("Réponse courte")
    TEXTE_LONG = "TL", _("Paragraphe")
    CHOIX_UNIQUE = "CU", _("Choix unique")
    CHOIX_MULTIPLES = "CM", _("Choix multiples")
    LISTE_DEROUlANTE = "LD", _("Liste déroulante")
    DATE = "DT", _("Date")
    FICHIER = "FL", _("Fichier")
    BOOLEEN = "BL", _("Oui/Non")


class Question(models.Model):
    libelle = models.CharField(_("Libellé de la question"), max_length=255)
    type_question = models.CharField(
        _("Type de question"), max_length=2, choices=QuestionType.choices
    )
    options = models.TextField(
        _("Options pour les choix"),
        blank=True,
        help_text=_("Séparer les options par des points-virgules (;)"),
    )
    obligatoire = models.BooleanField(_("Obligatoire"), default=True)
    ordre = models.PositiveIntegerField(_("Ordre d'affichage"), default=0)
    aide_texte = models.TextField(_("Texte d'aide"), blank=True)

    class Meta:
        ordering = ["ordre"]

    def __str__(self):
        return self.libelle

    def get_options_list(self):
        if self.options:
            return [opt.strip() for opt in self.options.split(";")]
        return []


class SectionQuestionnaire(models.Model):
    nom = models.CharField(_("Nom de la section"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    ordre = models.PositiveIntegerField(_("Ordre d'affichage"), default=0)
    questions = models.ManyToManyField(Question, through="SectionQuestion")

    class Meta:
        ordering = ["ordre"]
        verbose_name = _("Section du questionnaire")
        verbose_name_plural = _("Sections du questionnaire")

    def __str__(self):
        return self.nom


class SectionQuestion(models.Model):
    section = models.ForeignKey(SectionQuestionnaire, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    ordre = models.PositiveIntegerField(_("Ordre dans la section"), default=0)

    class Meta:
        ordering = ["ordre"]
        unique_together = ("section", "question")


class Questionnaire(models.Model):
    nom = models.CharField(_("Nom du questionnaire"), max_length=100)
    sections = models.ManyToManyField(SectionQuestionnaire)
    actif = models.BooleanField(_("Actif"), default=True)
    date_creation = models.DateTimeField(_("Date de création"), auto_now_add=True)
    image_fr = models.ImageField(
        _("Image (FR)"), upload_to="evenements/", blank=True, null=True
    )
    image_en = models.ImageField(
        _("Image (EN)"), upload_to="evenements/", blank=True, null=True
    )
    image_it = models.ImageField(
        _("Image (IT)"), upload_to="evenements/", blank=True, null=True
    )

    def __str__(self):
        return self.nom


class Evenement(models.Model):
    titre = models.CharField(_("Titre"), max_length=200)
    description_fr = CKEditor5Field("Contenu en français", config_name="default")
    description_en = CKEditor5Field("Contenu en anglais", blank=True, null=True)
    description_it = CKEditor5Field("Contenu en italien", blank=True, null=True)
    image = models.ImageField(_("Image"), upload_to="evenements/")
    image_fr = models.ImageField(
        _("Image (FR)"), upload_to="evenements/", blank=True, null=True
    )
    image_en = models.ImageField(
        _("Image (EN)"), upload_to="evenements/", blank=True, null=True
    )
    image_it = models.ImageField(
        _("Image (IT)"), upload_to="evenements/", blank=True, null=True
    )
    image_fr1 = models.ImageField(
        _("Image 1 (FR)"), upload_to="evenements/", blank=True, null=True
    )
    image_en2 = models.ImageField(
        _("Image 2 (EN)"), upload_to="evenements/", blank=True, null=True
    )
    image_it3 = models.ImageField(
        _("Image 3 (IT)"), upload_to="evenements/", blank=True, null=True
    )
    date_debut = models.DateTimeField(_("Date de début"))
    date_fin = models.DateTimeField(_("Date de fin"))
    est_actif = models.BooleanField(_("Actif"), default=False)
    slug = models.SlugField(unique=True, blank=True)
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Questionnaire d'inscription"),
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre)

        now = timezone.now()
        if now < self.date_debut:
            self.est_actif = True
        else:
            self.est_actif = False

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre

    def count_interesses(self):
        return self.interetevenement_set.filter(interesse=True).count()

    def update_activation_status(self):
        """Méthode pour mettre à jour manuellement le statut d'activation"""
        now = timezone.now()
        if now < self.date_debut:
            self.est_actif = True
        else:
            self.est_actif = False
        self.save(update_fields=["est_actif"])

    def statut_evenement(self):
        """Retourne le statut textuel de l'événement"""
        now = timezone.now()
        if now < self.date_debut:
            return _("À venir")
        elif self.date_debut <= now <= self.date_fin:
            return _("En cours")
        else:
            return _("Terminé")

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


class ReponseQuestion(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    inscription = models.ForeignKey(
        "InteretEvenement", on_delete=models.CASCADE, related_name="reponses"
    )
    valeur = models.TextField(_("Réponse"))
    fichier = models.FileField(
        _("Fichier uploadé"), upload_to="reponses/fichiers/", blank=True, null=True
    )

    class Meta:
        verbose_name = _("Réponse à une question")
        verbose_name_plural = _("Réponses aux questions")
        unique_together = ("question", "inscription")

    def __str__(self):
        return f"Réponse à {self.question.libelle}"


def generate_reference():
    from evenements.models import InteretEvenement

    while True:
        ref = str(uuid.uuid4())[:12].upper()
        if not InteretEvenement.objects.filter(reference=ref).exists():
            return ref


class InteretEvenement(models.Model):
    utilisateur = models.ForeignKey(
        "accounts.Utilisateur", null=True, blank=True, on_delete=models.SET_NULL
    )
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE)

    # Informations de base (toujours requises)
    nom_complet = models.CharField(_("Nom complet"), max_length=100)
    email = models.EmailField(_("Email"))
    telephone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    interesse = models.BooleanField(_("Je souhaite participer"), default=False)
    # reference = models.CharField(max_length=20,default=generate_reference, null=True, blank=True)

    accepte_newsletter = models.BooleanField(
        _("J'accepte de recevoir des informations sur les futurs événements"),
        default=False,
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Inscription à l'événement")
        verbose_name_plural = _("Inscriptions aux événements")
        unique_together = ("email", "evenement")

    def __str__(self):
        return f"{self.nom_complet} - {self.evenement.titre}"

    def get_reponse_for_question(self, question):
        reponse = self.reponses.filter(question=question).first()
        if reponse:
            if question.type_question == QuestionType.BOOLEEN:
                return reponse.valeur.lower() in ("true", "1", "oui", "yes", "o", "y")
            return reponse.valeur
        return None

    def set_reponse_for_question(self, question, valeur):
        """
        Crée ou met à jour une réponse à une question pour cette inscription.
        On enregistre toujours dans le champ 'valeur' (texte).
        """
        # Normaliser la valeur selon le type de la question
        if question.type_question == QuestionType.BOOLEEN:
            valeur = (
                "Oui"
                if str(valeur).strip().lower() in ["oui", "yes", "true", "1", "o", "y"]
                else "Non"
            )
        else:
            valeur = str(valeur).strip()

        reponse, created = self.reponses.update_or_create(
            question=question,
            defaults={"valeur": valeur},
        )
        return reponse
