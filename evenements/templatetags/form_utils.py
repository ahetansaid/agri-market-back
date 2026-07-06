from django import template

register = template.Library()


@register.filter
def get_form_field(form, field_name):
    """Retourne un champ spécifique du formulaire"""
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter
def get_field(form, field_name):
    """Version plus robuste avec debug intégré"""
    try:
        if field_name not in form.fields:
            raise ValueError(f"Champ {field_name} absent de form.fields")
        return form[field_name]
    except Exception as e:
        print(f"ERREUR dans get_field({field_name}): {str(e)}")  # Log dans la console
        return None


@register.filter
def field_exists(form, field_name):
    """Version avec vérification plus stricte"""
    return hasattr(form, "fields") and field_name in form.fields


@register.filter
def multiply(value, arg):
    """Multiplie la valeur par l'argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value


@register.filter(name="field_type")
def field_type(field):
    return field.field.__class__.__name__
