from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from .models import InteretEvenement, Question, ReponseQuestion


class DynamicEventForm(forms.Form):
    def __init__(self, *args, questionnaire=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Champs de base fixes
        self.fields["nom_complet"] = forms.CharField(
            label=_("Nom complet"),
            max_length=100,
            required=True,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
        self.fields["email"] = forms.EmailField(
            label=_("Email"),
            required=True,
            widget=forms.EmailInput(attrs={"class": "form-control"}),
        )
        self.fields["telephone"] = forms.CharField(
            label=_("Téléphone"),
            max_length=20,
            required=False,
            widget=forms.TextInput(attrs={"class": "form-control"}),
        )
        self.fields["interesse"] = forms.BooleanField(
            label=_("Je souhaite participer"),
            initial=False,
            required=False,
            widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        )

        # self.fields["reference"] = forms.CharField(
        #     label=_("Reférence"),
        #     max_length=20,
        #     required=False,
        #     widget=forms.TextInput(attrs={"class": "form-control"}),
        # )
        self.fields["accepte_newsletter"] = forms.BooleanField(
            label=_("J'accepte de recevoir des newsletters"),
            initial=False,
            required=False,
            widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        )

        # Ajout des champs dynamiques si questionnaire existe
        if questionnaire:
            for section in questionnaire.sections.prefetch_related(
                "sectionquestion_set__question"
            ).all():
                for sq in section.sectionquestion_set.select_related(
                    "question"
                ).order_by("ordre"):
                    self.add_question_field(sq.question)

    def add_question_field(self, question):

        # print(f"[DEBUG] {question.id=} {question.libelle=} {question.type_question=}")

        field_name = f"question_{question.id}"
        field_kwargs = {
            "label": question.libelle,
            "required": question.obligatoire,
            "help_text": question.aide_texte,
        }

        if question.type_question == "TC":  # Texte court
            self.fields[field_name] = forms.CharField(
                widget=forms.TextInput(attrs={"class": "form-control"}), **field_kwargs
            )
        elif question.type_question.strip().upper() == "TL":  # Texte long

            self.fields[field_name] = forms.CharField(
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
                **field_kwargs,
            )
        elif question.type_question == "CU":  # Choix unique
            choices = [(opt, opt) for opt in question.get_options_list()]
            self.fields[field_name] = forms.ChoiceField(
                choices=choices,
                widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
                **field_kwargs,
            )
        elif question.type_question == "CM":  # Choix multiples
            choices = [(opt, opt) for opt in question.get_options_list()]
            self.fields[field_name] = forms.MultipleChoiceField(
                choices=choices, widget=forms.CheckboxSelectMultiple(), **field_kwargs
            )
        elif question.type_question == "LD":  # Liste déroulante
            choices = [(opt, opt) for opt in question.get_options_list()]
            self.fields[field_name] = forms.ChoiceField(
                choices=choices,
                widget=forms.Select(attrs={"class": "form-control"}),
                **field_kwargs,
            )
        elif question.type_question == "DT":  # Date
            self.fields[field_name] = forms.DateField(
                widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
                **field_kwargs,
            )
        elif question.type_question == "FL":  # Fichier
            self.fields[field_name] = forms.FileField(
                widget=forms.ClearableFileInput(
                    attrs={"class": "form-control", "onchange": "previewFile(this)"}
                ),
                **field_kwargs,
            )
        elif question.type_question == "BL":  # Booléen
            # Modification ici: on ne passe pas required dans field_kwargs
            widget_attrs = {"class": "form-check-input"}
            if question.obligatoire:
                widget_attrs["required"] = "required"

            self.fields[field_name] = forms.BooleanField(
                widget=forms.CheckboxInput(attrs=widget_attrs),
                label=question.libelle,
                help_text=question.aide_texte,
                required=question.obligatoire,
            )

    def save(self, evenement, utilisateur=None):
        inscription_data = {
            "nom_complet": self.cleaned_data["nom_complet"],
            "email": self.cleaned_data["email"],
            "telephone": self.cleaned_data.get("telephone", ""),
            "interesse": self.cleaned_data.get("interesse", True),
            "accepte_newsletter": self.cleaned_data.get("accepte_newsletter", True),
            "utilisateur": utilisateur,
        }

        inscription, created = InteretEvenement.objects.update_or_create(
            email=self.cleaned_data["email"],
            evenement=evenement,
            defaults=inscription_data,
        )

        # Sauvegarde des réponses aux questions
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith("question_"):
                question_id = int(field_name.split("_")[1])
                question = Question.objects.get(id=question_id)

                # Supprimer l'ancienne réponse si elle existe
                inscription.reponses.filter(question=question).delete()

                if question.type_question == "FL" and isinstance(value, UploadedFile):
                    ReponseQuestion.objects.create(
                        question=question,
                        inscription=inscription,
                        valeur=value.name,
                        fichier=value,
                    )
                elif question.type_question == "CM":
                    ReponseQuestion.objects.create(
                        question=question,
                        inscription=inscription,
                        valeur=";".join(value) if value else "",
                    )
                else:
                    ReponseQuestion.objects.create(
                        question=question,
                        inscription=inscription,
                        valeur=str(value) if value is not None else "",
                    )

        return inscription
