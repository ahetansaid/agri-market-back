"""Cross-cutting security utilities (HTML sanitization, file upload validators)."""

from __future__ import annotations

import os

import nh3
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# ---------------------------------------------------------------------------
# HTML sanitization (defense against stored XSS via CKEditor content)
# ---------------------------------------------------------------------------

_ALLOWED_TAGS = nh3.ALLOWED_TAGS | {
    "img",
    "figure",
    "figcaption",
    "span",
    "div",
    "section",
}

_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    **nh3.ALLOWED_ATTRIBUTES,
    "img": {"src", "alt", "title", "width", "height", "class", "style"},
    # NB : on n'autorise pas "rel" sur <a> car link_rel le gere
    # automatiquement (nh3 ajoute noopener noreferrer en sortie)
    "a": {"href", "title", "target", "class"},
    "*": {"class", "id", "style"},
}

_ALLOWED_URL_SCHEMES = {"http", "https", "mailto", "tel"}


def sanitize_html(html: str | None) -> str:
    """Strip dangerous tags/attributes from user-provided HTML (CKEditor output)."""
    if not html:
        return ""
    return nh3.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer",
    )


# ---------------------------------------------------------------------------
# File upload validators
# ---------------------------------------------------------------------------

# 10 MB par défaut
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".csv",
    ".zip",
}

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
}

BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".ps1",
    ".scr",
    ".com",
    ".msi",
    ".js",
    ".vbs",
    ".jar",
    ".php",
    ".py",
    ".rb",
    ".pl",
    ".html",
    ".htm",
    ".svg",
}


def _check_size(file_obj, max_size: int = MAX_UPLOAD_SIZE) -> None:
    size = getattr(file_obj, "size", None)
    if size is not None and size > max_size:
        raise ValidationError(
            _("Le fichier dépasse la taille maximale de %(max)s Mo.")
            % {"max": max_size // (1024 * 1024)}
        )


def _check_extension(file_obj, allowed: set[str]) -> str:
    name = getattr(file_obj, "name", "") or ""
    ext = os.path.splitext(name)[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        raise ValidationError(
            _("Le type de fichier '%(ext)s' n'est pas autorisé.") % {"ext": ext}
        )
    if ext not in allowed:
        raise ValidationError(
            _("Extension non autorisée. Acceptées : %(allowed)s.")
            % {"allowed": ", ".join(sorted(allowed))}
        )
    return ext


def validate_document_upload(file_obj) -> None:
    """Validateur pour les pièces jointes (messagerie, documents)."""
    _check_size(file_obj)
    _check_extension(file_obj, ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS)


def validate_image_upload(file_obj) -> None:
    """Validateur pour les images (annonces, profil, messagerie image)."""
    _check_size(file_obj, max_size=5 * 1024 * 1024)
    _check_extension(file_obj, ALLOWED_IMAGE_EXTENSIONS)
