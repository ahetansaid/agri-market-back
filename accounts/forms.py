from django import forms
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeView
from django.contrib.auth.forms import SetPasswordForm, UserChangeForm, UserCreationForm
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Societe, Utilisateur


class UtilisateurForm(UserCreationForm):
    is_company = forms.BooleanField(
        label=_("Je suis une entreprise"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Utilisateur
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
            "individual_category",
            "telephone",
            "pays",
            "ville",
            "code_postal",
            "adresse",
            "picture",
            "is_company",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["individual_category"].required = False
        self.fields["first_name"].required = False
        self.fields["last_name"].required = False

        common_attrs = {
            "class": "form-control form-control-lg border border-success",
            "style": "background-color: #ffffff; padding: 12px;",
        }

        # Configuration des champs
        for field_name, field in self.fields.items():
            if field_name not in ["is_company", "picture"]:
                field.widget.attrs.update(common_attrs)

        self.fields["picture"].widget.attrs.update({"class": "form-control"})
        self.fields["pays"].widget.attrs.update(
            {"class": "form-select select2-country"}
        )

    def clean(self):
        cleaned_data = super().clean()
        is_company = cleaned_data.get("is_company")

        # Définir le type utilisateur
        self.instance.user_type = "entreprise" if is_company else "individu"

        if is_company:
            # Nettoyage côté instance, PAS cleaned_data
            self.instance.first_name = ""
            self.instance.last_name = ""
            self.instance.individual_category = None
        else:
            if not cleaned_data.get("first_name"):
                self.add_error(
                    "first_name", _("Ce champ est obligatoire pour les individus")
                )
            if not cleaned_data.get("last_name"):
                self.add_error(
                    "last_name", _("Ce champ est obligatoire pour les individus")
                )
            if not cleaned_data.get("individual_category"):
                self.add_error(
                    "individual_category",
                    _("Ce champ est obligatoire pour les individus"),
                )

        return cleaned_data


class SocieteForm(forms.ModelForm):
    class Meta:
        model = Societe
        fields = [
            "nom",
            "company_type",
            "autre_type",
            "code_commercial",
            "produits_vendus",
            "produits_recherches",
        ]
        widgets = {
            "nom": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg border border-success",
                    "style": "background-color: #ffffff; padding: 12px;",
                    "placeholder": _("Nom de la société"),
                }
            ),
            "company_type": forms.Select(
                attrs={
                    "class": "form-control form-control-lg border border-success",
                    "style": "background-color: #ffffff; padding: 12px;",
                }
            ),
            "autre_type": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg border border-success",
                    "style": "background-color: #ffffff; padding: 12px;",
                    "placeholder": _('Précisez le type si "Autre"'),
                }
            ),
            "code_commercial": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg border border-success",
                    "style": "background-color: #ffffff; padding: 12px;",
                    "placeholder": _("Code du commercial référent"),
                }
            ),
            "produits_vendus": forms.SelectMultiple(
                attrs={
                    "class": "form-control form-control-lg border border-success",
                    "style": "background-color: #ffffff; padding: 12px;",
                }
            ),
            "produits_recherches": forms.SelectMultiple(
                attrs={
                    "class": "form-control form-control-lg border border-success",
                    "style": "background-color: #ffffff; padding: 12px;",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        company_type = cleaned_data.get("company_type")
        autre_type = cleaned_data.get("autre_type")

        if company_type == Societe.CompanyType.AUTRE and not autre_type:
            raise ValidationError(
                {"autre_type": _("Veuillez préciser le type d'entreprise")}
            )

        return cleaned_data


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "class": "form-control"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update(
            {
                "placeholder": _("Entrez votre e-mail  "),
                "required": True,
                "class": "form-control",
            }
        )


class CustomPasswordResetConfirmForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].widget.attrs.update({"class": "form-control"})
        self.fields["new_password2"].widget.attrs.update({"class": "form-control"})


class UtilisateurChangeForm(UserChangeForm):

    class Meta:
        model = Utilisateur
        exclude = [
            "id",
            "password",
            "password1",
            "password2",
            "last_login",
            "is_superuser",
            "is_active",
            "user_permissions",
            "date_joined",
            "is_staff",
            "groups",
            "archive",
            "username",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update(
            {"placeholder": _("Enter your e-mail address"), "required": True}
        )
        self.fields["username"].widget.attrs.update(
            {
                "placeholder": _("Choose a user name"),
                "autofocus": False,
                "disabled": True,
                "required": False,
            }
        )
        self.fields["picture"].widget.attrs.update(
            {"placeholder": _("Enter your picture")}
        )


class PasswordChangeForm(BasePasswordChangeView):

    old_password = forms.CharField(
        label=("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autofocus": True}),
    )
    field_order = ["old_password", "new_password1", "new_password2"]

    class Meta:
        model = Utilisateur
        exclude = [
            "id",
            "password",
            "last_login",
            "last_name",
            "last_login",
            "groups",
            "is_superuser",
            "is_active",
            "user_permissions",
            "date_joined",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update({"class": "form-control"})
        self.fields["new_password1"].widget.attrs.update({"class": "form-control"})
        self.fields["new_password2"].widget.attrs.update({"class": "form-control"})

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        return old_password


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["first_name", "last_name", "email", "telephone", "adresse"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
        }


class ProfilUtilisateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = [
            "first_name",
            "last_name",
            "email",
            "telephone",
            "adresse",
            "ville",
            "pays",
            "code_postal",
            "picture",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "ville": forms.TextInput(attrs={"class": "form-control"}),
            "pays": forms.TextInput(attrs={"class": "form-control"}),
            "code_postal": forms.TextInput(attrs={"class": "form-control"}),
            "picture": forms.TextInput(attrs={"class": "form-control"}),
        }
