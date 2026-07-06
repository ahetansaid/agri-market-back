# cron.py

import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Announcement


# utils.py
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def validate_products():
    # SECURITE : l'auto-approbation contourne entierement le workflow de
    # double validation humaine (et les controles clean_* du formulaire).
    # Desactive par defaut ; ne s'execute que si explicitement active via
    # AUTO_APPROVE_ANNOUNCEMENTS=True dans les settings. Ne jamais approuver
    # les brouillons (status="draft"), qui n'ont pas ete soumis.
    if not getattr(settings, "AUTO_APPROVE_ANNOUNCEMENTS", False):
        return

    threshold = timezone.now() - timedelta(minutes=1)

    Announcement.objects.filter(
        status__in=["pending_first", "pending_second"],
        publication_date__lte=threshold,
    ).update(status="approved")


# -----------------------------
# REGEX compilées
# -----------------------------

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"\b\d{8,14}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")

PHONE_WORDS_REGEX = re.compile(
    r"\b(zero|one|two|three|four|five|six|seven|eight|nine|"
    r"un|deux|trois|quatre|cinq|six|sept|huit|neuf)\b",
    re.IGNORECASE,
)

URL_REGEX = re.compile(r"(https?://[^\s]+|www\.[^\s]+)", re.IGNORECASE)
POSTAL_REGEX = re.compile(r"\b\d{5}\b")

CONTACT_WORDS_REGEX = re.compile(
    r"(whatsapp|telegram|contact|call\s?me|instagram|facebook|dm)",
    re.IGNORECASE,
)


# -----------------------------
# conversion mots → chiffres
# -----------------------------

NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "zéro": "0",
    "un": "1",
    "deux": "2",
    "trois": "3",
    "quatre": "4",
    "cinq": "5",
    "six": "6",
    "sept": "7",
    "huit": "8",
    "neuf": "9",
}

MEASURE_UNITS = [
    "rpm",
    "hp",
    "kw",
    "kg",
    "g",
    "m/min",
    "m/s",
    "km/h",
    "km",
    "m",
    "tonne",
    "ton",
    "t",
    "l",
    "litre",
    "litres",
    "ml",
    "bar",
    "psi",
    "v",
    "volt",
    "a",
    "amp",
]


def normalize_numbers(text):

    words = text.lower().split()

    converted = []

    for word in words:
        converted.append(NUMBER_WORDS.get(word, word))

    return " ".join(converted)


# -----------------------------
# nettoyage texte
# -----------------------------


def clean_text(text):

    text = normalize_numbers(text)

    text = re.sub(r"[^\w]", "", text)

    return text


# -----------------------------
# détection numéro caché
# -----------------------------


def detect_hidden_phone(text):

    text = clean_text(text)

    hidden_phone_regex = re.compile(r"\d{8,14}")

    return bool(hidden_phone_regex.search(text))


# -----------------------------
# Supprime les numéros de liste au début des lignes
# -----------------------------


def remove_list_numbers(text):
    """
    Supprime les numéros de liste au début des lignes
    Exemple:
    1.Text
    2.Text
    10.Text
    """

    return re.sub(r"(?m)^\s*\d{1,2}\.\s*", "", text)


# -----------------------------
# Supprime les valeurs techniques exemple: 540 rpm, 80 kw, 1500 kg
# -----------------------------


def remove_measurements(text):
    """
    Supprime les valeurs techniques
    exemple: 540 rpm, 80 kw, 1500 kg
    """

    unit_pattern = "|".join(MEASURE_UNITS)

    pattern = rf"\b\d+(?:[.,]\d+)?\s*(?:{unit_pattern})\b"

    return re.sub(pattern, "", text, flags=re.IGNORECASE)


# -----------------------------
# fonction principale
# -----------------------------


def contains_forbidden_info(text):

    if not text:
        return False

    # supprimer les numéros de liste
    text = remove_list_numbers(text)
    # supprimer valeurs techniques
    text = remove_measurements(text)

    # détecter numéro caché
    if detect_hidden_phone(text):
        return True

    return any(
        regex.search(text)
        for regex in [
            EMAIL_REGEX,
            PHONE_REGEX,
            PHONE_WORDS_REGEX,
            URL_REGEX,
            POSTAL_REGEX,
            CONTACT_WORDS_REGEX,
        ]
    )


# -----------------------------
# vérification des annonces
# -----------------------------


def check_product_descriptions():

    products = Announcement.objects.select_related("user").all()

    for product in products:

        if contains_forbidden_info(product.description):

            # éviter plusieurs emails
            # if not product.flagged:

            #     product.flagged = True
            #     product.status = "rejected"
            #     product.flagged_date = timezone.now()

            #     product.save(update_fields=["flagged", "status", "flagged_date"])

            send_admin_notification(product)
            send_user_notification(product)


# -------------------------
# Email administrateur
# -------------------------


def send_admin_notification(product):

    subject = f"⚠️ Information sensible détectée : {product.product_name}"

    message = (
        f"Une information sensible a été détectée dans une annonce.\n\n"
        f"Produit : {product.product_name}\n"
        f"Utilisateur : {product.user}\n"
        f"ID annonce : {product.id}\n\n"
        f"Veuillez vérifier cette annonce."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [
            "briceklaus@gmail.com",
            "klausyakpa@gmail.com",
        ],
        fail_silently=False,
    )


# -------------------------
# Email annonceur
# -------------------------


def send_user_notification(product):

    subject = "Votre annonce ne respecte pas les conditions d'utilisation"

    message = f"""
        Bonjour {product.user},

        Votre annonce intitulée "{product.product_name}" ne respecte pas les règles de notre plateforme.

        ❗ Conditions de transmission :

        Aucune coordonnée, ni nom d'entreprise, ni adresse web, ne peuvent être indiqués dans votre description.

        En cliquant sur "Enregistrer", vous acceptez que votre description soit lue et contrôlée automatiquement par nos systèmes avant sa publication.

        Toute tentative de dissimulation de coordonnées entraînera la suppression pure et simple du compte et des comptes associés sans possibilité de réinscription.

        Merci de modifier votre annonce afin de supprimer toute information de contact.

        Cordialement,
        L'équipe de la plateforme
        """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [product.user.email],
        fail_silently=True,
    )


def send_keyword_notifications():
    # Obtenez les annonces publiées dans les 5 dernières minutes
    now = timezone.now().date()
    five_minutes_ago = now - timezone.timedelta(minutes=2)
    recent_announcements = Announcement.objects.filter(createdat__date=five_minutes_ago)

    # Parcourez les utilisateurs et leurs mots-clés
    for notification in Announcement.objects.all():
        user = notification.user
        keyword = notification.name

        # Filtrez les annonces qui contiennent le mot-clé
        matching_announcements = recent_announcements.filter(
            description__icontains=keyword
        )

        if matching_announcements.exists():
            # Créez le message de notification avec les liens
            message = f"Bonjour {user.username},\n\nVoici les nouvelles annonces correspondant à vos mots-clés :\n\n"
            for ann in matching_announcements:
                announcement_url = (
                    settings.SITE_URL + "/detpaysailproduit/" + str(ann.pk)
                )
                subject = f"AN:{ann.reference}/ {ann.nomduproduit}/ {ann.pays}/ {ann.typeannonce}"  # Crée l'URL complète
                message += (
                    f"{subject}\n {ann.description}\nLien: {announcement_url}\n\n"
                )

            # Envoyez l'e-mail avec les annonces et leurs liens
            send_mail(
                "Nouvelles annonces correspondant à vos mots-clés",
                message,
                "klausyakpa@gmail.com",
                [user.email],
                fail_silently=False,
            )
