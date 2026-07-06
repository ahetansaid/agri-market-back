"""Validateurs marketplace.

- validate_file_size : taille max upload
- detect_contact_info / format_violation_message : detection de coordonnees
  personnelles dans le contenu utilisateur (annonces, messages)
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _


def validate_file_size(value):
    filesize = value.size

    if filesize > 4485760:
        raise ValidationError("The maximum file size that can be uploaded is 04MB")
    return value


# ---------------------------------------------------------------------------
# Anti-coordonnees : detection regex
# ---------------------------------------------------------------------------

# Numero de telephone : entre 8 et 16 chiffres apres nettoyage des separateurs
_PHONE_RAW = re.compile(r"(?:\+|00)?\d[\d\s.\-()]{7,}\d")

# Email
_EMAIL = re.compile(
    r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)

# URL avec http(s) ou www
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)

# Domaine sans protocole : "monsite.com" avec TLD whitelist (limite faux positifs)
_TLDS = (
    "com", "net", "org", "info", "biz", "africa", "shop", "store",
    "fr", "be", "ch", "ca", "io", "co", "us", "uk", "eu",
    "ng", "ci", "sn", "ml", "bj", "tg", "bf", "gh", "cm", "ma",
    "tn", "dz", "eg", "ke", "tz", "ug", "rw", "et", "za",
)
_DOMAIN = re.compile(
    r"\b[a-z0-9][a-z0-9\-]{1,62}\.(?:" + "|".join(_TLDS) + r")\b",
    re.IGNORECASE,
)

# Pseudo reseau social : @pseudo (au moins 3 chars apres @)
_HANDLE = re.compile(r"@[A-Za-z][\w.\-]{2,}")

# IBAN simplifie : 2 lettres + 2 chiffres + suite
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[\s\d]{12,}\b")


def detect_contact_info(text: str) -> list[tuple[str, str]]:
    """Retourne [(type, valeur), ...] des coordonnees detectees.

    Vide si rien. Types : telephone, email, url, domaine, pseudo, iban.
    """
    if not text:
        return []

    # Strip HTML CKEditor pour analyser le texte brut
    plain = strip_tags(text)

    matches: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, value: str) -> None:
        key = (kind, value.lower().strip())
        if key not in seen:
            seen.add(key)
            matches.append((kind, value.strip()))

    # Telephone : on enleve emails+URLs d'abord pour ne pas capturer
    # leurs chiffres comme telephones
    sanitized = _EMAIL.sub(" ", plain)
    sanitized = _URL.sub(" ", sanitized)
    for m in _PHONE_RAW.finditer(sanitized):
        digits = re.sub(r"\D", "", m.group())
        if 8 <= len(digits) <= 16:
            add("telephone", m.group())

    for m in _EMAIL.finditer(plain):
        add("email", m.group())

    for m in _URL.finditer(plain):
        add("url", m.group())

    plain_no_url = _URL.sub(" ", plain)
    for m in _DOMAIN.finditer(plain_no_url):
        add("domaine", m.group())

    for m in _HANDLE.finditer(plain):
        ctx = plain[max(0, m.start() - 1) : m.start()]
        # Exclure les emails (le @ est precede d'un caractere de mot)
        if ctx and ctx[-1] not in " \t\n\r,;\xa0":
            continue
        add("pseudo", m.group())

    for m in _IBAN.finditer(plain):
        add("iban", m.group())

    return matches


_TYPE_LABELS = {
    "telephone": _("numero de telephone"),
    "email": _("adresse email"),
    "url": _("lien internet"),
    "domaine": _("nom de domaine / site web"),
    "pseudo": _("pseudo reseau social"),
    "iban": _("coordonnees bancaires"),
}


def format_violation_message(matches: list[tuple[str, str]]) -> str:
    """Compose un message d'erreur lisible pour le user."""
    if not matches:
        return ""

    by_type: dict[str, list[str]] = {}
    for kind, val in matches:
        by_type.setdefault(kind, []).append(val)

    parts = []
    for kind, values in by_type.items():
        label = _TYPE_LABELS.get(kind, kind)
        sample = ", ".join(values[:3])
        if len(values) > 3:
            sample += f" (+{len(values) - 3})"
        parts.append(f"{label} ({sample})")

    return _(
        "Coordonnees personnelles detectees : %(items)s. Aucune coordonnee "
        "(telephone, email, site web, adresse) ne peut figurer dans une "
        "annonce. Retirez-les pour pouvoir soumettre votre annonce."
    ) % {"items": " ; ".join(parts)}
