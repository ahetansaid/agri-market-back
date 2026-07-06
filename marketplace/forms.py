from ckeditor.widgets import CKEditorWidget
from django import forms
from django.utils.translation import gettext_lazy as _
from django_countries import countries

from accounts.models import AFRICAN_COUNTRY_CODES

from .validators import detect_contact_info, format_violation_message

from .models import (
    Announcement,
    AnnouncementType,
    Category,
    SubCategory,
)


class AnnouncementForm(forms.ModelForm):
    description = forms.CharField(
        widget=CKEditorWidget(config_name="default", attrs={"class": "form-control"}),
        label=_("Description détaillée"),
        required=True,
    )
    caracteristiques = forms.CharField(
        widget=CKEditorWidget(config_name="default", attrs={"class": "form-control"}),
        label=_("Caractéristiques ou spécifications"),
        required=False,
    )

    class Meta:
        model = Announcement
        fields = [
            "title",
            "product_name",
            "category",
            "subcategory",
            "type",
            "description",
            "caracteristiques",
            "brand",
            "variety",
            "quantity",
            "unit",
            "is_organic",
            "country",
            "shipping_conditions",
            "transaction_details",
            "restrictions",
            "tags",
            "image",
        ]
        widgets = {
            "publication_date": forms.HiddenInput(),
            "tags": forms.TextInput(
                attrs={"data-role": "tagsinput", "class": "form-control"}
            ),
            "image": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg, image/png",
                    "data-max-size": "500",
                    "rerequired": "False",
                }
            ),
        }
        help_texts = {
            "image": _("Image illustrative (max 500KB, 800x600px)"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if "type" in self.data:
            announcement_type = self.data.get("type")
            self.fields["product_name"].required = announcement_type in [
                AnnouncementType.SALE.value,
                AnnouncementType.PURCHASE.value,
            ]
        elif self.instance.pk:
            self.fields["product_name"].required = self.instance.type in [
                AnnouncementType.SALE.value,
                AnnouncementType.PURCHASE.value,
            ]

        # Configuration CSS
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput)):
                field.widget.attrs.update({"class": "form-control"})

        # Filtrage pays africains
        # self.fields["country"].choices = [
        #     (code, name) for code, name in countries if code in AFRICAN_COUNTRY_CODES
        # ]
        self.fields["country"].widget.attrs.update(
            {"class": "form-select select2-country"}
        )

        # Pré-remplir le pays utilisateur
        if self.user and self.user.pays:
            self.fields["country"].initial = self.user.pays

        # Sous-catégories dynamiques
        self.fields["subcategory"].queryset = SubCategory.objects.none()

        if "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = (
                    Category.objects.get(id=category_id)
                    .subcategories.all()
                    .order_by("name")
                )
            except (ValueError, TypeError, Category.DoesNotExist):
                pass

        elif self.instance.pk and self.instance.category:
            self.fields["subcategory"].queryset = (
                self.instance.category.subcategories.all().order_by("name")
            )

        # self.fields["subcategory"].queryset = SubCategory.objects.none()

        # if "category" in self.data:
        #     try:
        #         category_id = int(self.data.get("category"))
        #         self.fields["subcategory"].queryset = SubCategory.objects.filter(
        #             category_id=category_id
        #         )
        #     except (ValueError, TypeError):
        #         pass
        # elif self.instance.pk and self.instance.category:
        #     self.fields["subcategory"].queryset = self.instance.category.subcategories.all()

        # Meilleur placeholder pour les tags
        self.fields["tags"].widget.attrs["placeholder"] = _("ex: agricole, bio, local")

        # Type par défaut
        if not self.instance.pk:
            self.fields["type"].initial = AnnouncementType.SALE

    def clean(self):
        cleaned_data = super().clean()
        announcement_type = cleaned_data.get("type")

        # Validation conditionnelle
        if announcement_type in [AnnouncementType.SALE, AnnouncementType.PURCHASE]:
            if not cleaned_data.get("product_name"):
                self.add_error(
                    "product_name", _("Ce champ est requis pour ce type d'annonce")
                )
            if not cleaned_data.get("quantity"):
                self.add_error(
                    "quantity", _("Ce champ est requis pour ce type d'annonce")
                )
            if not cleaned_data.get("unit"):
                self.add_error("unit", _("Ce champ est requis pour ce type d'annonce"))

        return cleaned_data

    def clean_description(self):
        """Refuse l'annonce si la description contient des coordonnees
        personnelles (telephone, email, URL, etc.)."""
        desc = self.cleaned_data.get("description", "")
        matches = detect_contact_info(desc)
        if matches:
            raise forms.ValidationError(format_violation_message(matches))
        return desc

    def clean_caracteristiques(self):
        """Idem pour les caracteristiques."""
        car = self.cleaned_data.get("caracteristiques", "")
        matches = detect_contact_info(car)
        if matches:
            raise forms.ValidationError(format_violation_message(matches))
        return car

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "file"):
            if image.size > 500 * 1024:
                raise forms.ValidationError(
                    _(
                        "L'image ne doit pas dépasser 500KB, les dimenssion de l'image doivent être lon:740 px et hau:380 px"
                    )
                )
            if not image.name.lower().endswith((".jpg", ".jpeg", ".png")):
                raise forms.ValidationError(
                    _("Seuls les formats JPG/PNG sont acceptés")
                )
            # SECURITE : ne pas se fier a l'extension. Verifier que le contenu
            # est reellement une image JPEG/PNG (magic bytes) pour empecher
            # l'upload de fichiers arbitraires renommes en .jpg.
            from PIL import Image, UnidentifiedImageError

            try:
                image.seek(0)
                img = Image.open(image)
                img.verify()
                if img.format not in ("JPEG", "PNG"):
                    raise forms.ValidationError(
                        _("Seuls les formats JPG/PNG sont acceptés")
                    )
            except (UnidentifiedImageError, OSError):
                raise forms.ValidationError(
                    _("Le fichier fourni n'est pas une image valide")
                )
            finally:
                image.seek(0)
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user:
            instance.user = self.user

        if commit:
            instance.save()
            self.save_m2m()  # Pour les tags

        return instance


# Formulaire pour filtrer les annonces
class AnnouncementFilterForm(forms.Form):
    SEARCH_CHOICES = [
        ("title", _("Titre")),
        ("reference", _("Référence")),
        ("description", _("Description")),
    ]

    search_by = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial="title",
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )

    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Rechercher...")}
        ),
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_category"}),
    )

    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "id": "id_subcategory"}),
    )

    country = forms.ChoiceField(
        choices=[("", _("Tous les pays"))]
        + [(code, name) for code, name in countries if code in AFRICAN_COUNTRY_CODES],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    type = forms.ChoiceField(
        choices=[("", _("Tous types"))] + list(AnnouncementType.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamique des sous-catégories

        self.fields["subcategory"].queryset = SubCategory.objects.none()

        if "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = (
                    Category.objects.get(id=category_id)
                    .subcategories.all()
                    .order_by("name")
                )
            except (ValueError, TypeError, Category.DoesNotExist):
                pass

        elif self.instance.pk and self.instance.category:
            self.fields["subcategory"].queryset = (
                self.instance.category.subcategories.all().order_by("name")
            )

        # Ajouter un placeholder plus descriptif
        self.fields["search_term"].widget.attrs["placeholder"] = _(
            "Référence, titre ou description..."
        )
