"""Filtre Django pour rendre du HTML utilisateur (CKEditor) de maniere sure."""

from django import template
from django.utils.safestring import mark_safe

from idamarketplace.security import sanitize_html

register = template.Library()


@register.filter(name="safe_html", is_safe=True)
def safe_html(value):
    """Sanitize un fragment HTML (allowlist nh3) puis le marque safe.

    A utiliser a la place de `|safe` sur tout contenu venant d'un editeur
    riche (CKEditor 5, etc.) ou de l'utilisateur. Bloque scripts, iframes
    non autorises, gestionnaires on*, javascript: URLs, etc.
    """
    return mark_safe(sanitize_html(value or ""))
