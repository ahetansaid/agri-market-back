import phonenumbers
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordChangeView as BasePasswordChangeView
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)
from django.views import generic
from django.views.generic import View
from django_countries import countries

from accounts.forms import (
    CustomPasswordResetConfirmForm,
    PasswordChangeForm,
    ProfilUtilisateurForm,
    SocieteForm,
    UtilisateurChangeForm,
    UtilisateurForm,
)

from .models import Societe, Utilisateur


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"login": "active"})

    def post(self, request, *args, **kwargs):
        identifiant = request.POST.get("username")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        if identifiant and password:
            # Recherche de l'utilisateur par username ou email
            try:
                user = Utilisateur.objects.get(
                    Q(username=identifiant) | Q(email=identifiant)
                )
                auth_user = authenticate(username=user.username, password=password)
            except Utilisateur.DoesNotExist:
                auth_user = None

            if auth_user is not None and auth_user.is_active:
                login(request, auth_user)

                if not remember_me:
                    request.session.set_expiry(0)

                next_url = request.POST.get("next") or request.GET.get("next") or "/"
                if not url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    next_url = "/"
                return redirect(next_url)
            else:
                messages.error(
                    request, "Nom d'utilisateur/email ou mot de passe incorrect"
                )
        else:
            messages.error(request, "Veuillez remplir tous les champs")

        return render(request, self.template_name, {"login": "active"})


class LogoutView(generic.View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect("/")


class PasswordChangeDoneView(BasePasswordChangeView):
    template_name = "accounts/change_password_done.html"


class PasswordChangeView(BasePasswordChangeView):
    template_name = "accounts/passwordchange.html"
    form_class = PasswordChangeForm
    success_url = reverse_lazy("accounts:login")


def get_country_calling_codes():
    indicatifs = {}
    for code, name in countries:  # django-countries utilise cette structure
        try:
            phone_code = phonenumbers.country_code_for_region(code)
            indicatifs[code] = f"+{phone_code}"
        except phonenumbers.phonenumberutil.NumberParseException:
            continue
    return indicatifs


def register(request):
    user_form = UtilisateurForm(request.POST or None, request.FILES or None)

    societe_form = (
        SocieteForm(request.POST or None)
        if request.method == "POST" and request.POST.get("is_company") == "on"
        else SocieteForm()
    )

    if request.method == "POST":

        if user_form.is_valid():
            is_company = user_form.cleaned_data.get("is_company")

            if is_company and not societe_form.is_valid():
                messages.error(
                    request, "Veuillez corriger les erreurs du formulaire société."
                )
            else:
                # ===== Sauvegarde utilisateur =====
                user = user_form.save(commit=False)
                user.is_active = False
                user.user_type = "entreprise" if is_company else "individu"
                user.save()

                # ===== Sauvegarde société =====
                if is_company:
                    societe = societe_form.save(commit=False)
                    societe.utilisateur = user
                    societe.save()
                    societe_form.save_m2m()

                # ===== Envoi email activation =====
                current_site = (
                    getattr(settings, "SITE_DOMAIN", get_current_site(request).domain)
                    .replace("http://", "")
                    .replace("https://", "")
                )

                protocol = "https" if request.is_secure() else "http"

                context = {
                    "user": user,
                    "domain": current_site,
                    "protocol": protocol,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                }

                html_message = render_to_string("accounts/activate.html", context)
                text_message = strip_tags(html_message)

                email = EmailMultiAlternatives(
                    subject="Activez votre compte",
                    body=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                )
                email.attach_alternative(html_message, "text/html")

                #  IMPORTANT : PAS silencieux
                email.send(fail_silently=False)
                messages.success(
                    request, "Un email d'activation a été envoyé à votre adresse."
                )
                return redirect("accounts:email_sent")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    context = {
        "form": user_form,
        "societe_form": societe_form,
        "indicatifs": get_country_calling_codes(),
    }

    return render(request, "accounts/register.html", context)


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilisateur.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request,
            "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.",
        )
        return redirect(f"{reverse('accounts:login')}?activated=1")
    else:
        return render(request, "accounts/activation_invalid.html")


def email_sent(request):
    return render(request, "accounts/emails.html")


class UtilisateurUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Utilisateur
    form_class = UtilisateurChangeForm
    template_name = "accounts/update_utilisateur.html"
    success_url = "/indexadmin"

    def test_func(self):
        # Seul le proprietaire du compte ou un membre du staff peut editer
        # ce profil (empeche l'IDOR / prise de controle de compte par
        # modification de l'email d'un autre utilisateur).
        return self.request.user.is_staff or self.get_object().pk == self.request.user.pk


class UtilisateurListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = Utilisateur

    template_name = "accounts/list_user.html"

    def test_func(self):
        # La liste de tous les utilisateurs (PII) est reservee au staff.
        return self.request.user.is_staff


class ProfilUtilisateurView(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"

    def get(self, request, *args, **kwargs):
        utilisateur = request.user

        # Formulaire utilisateur
        form_user = ProfilUtilisateurForm(instance=utilisateur)

        # Formulaire entreprise si applicable
        form_entreprise = None
        if utilisateur.user_type == "entreprise":
            entreprise, _ = Societe.objects.get_or_create(utilisateur=utilisateur)
            form_entreprise = SocieteForm(instance=entreprise)

        return render(
            request,
            self.template_name,
            {"form_user": form_user, "form_entreprise": form_entreprise},
        )

    def post(self, request, *args, **kwargs):
        utilisateur = request.user

        # Gestion formulaire utilisateur
        form_user = ProfilUtilisateurForm(
            request.POST, request.FILES, instance=utilisateur
        )

        # Gestion formulaire entreprise si applicable
        form_entreprise = None
        if utilisateur.user_type == "entreprise":
            entreprise, _ = Societe.objects.get_or_create(utilisateur=utilisateur)
            form_entreprise = SocieteForm(
                request.POST, request.FILES, instance=entreprise
            )
        else:
            form_entreprise = None

        # Vérification des deux formulaires
        user_valid = form_user.is_valid()
        entreprise_valid = (
            True if form_entreprise is None else form_entreprise.is_valid()
        )

        if user_valid and entreprise_valid:
            form_user.save()
            if form_entreprise:
                form_entreprise.save()
            messages.success(request, _("Profil mis à jour avec succès."))
            return redirect("profil")
        else:
            messages.error(
                request, _("Veuillez corriger les erreurs dans le formulaire.")
            )

        return render(
            request,
            self.template_name,
            {"form_user": form_user, "form_entreprise": form_entreprise},
        )


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomPasswordResetConfirmForm
    template_name = "accounts/password_reset_confirm.html"

    def form_valid(self, form):
        messages.success(
            self.request,
            "Your password has been successfully reset. You can now log in with your new password.",
        )
        return super().form_valid(form)
