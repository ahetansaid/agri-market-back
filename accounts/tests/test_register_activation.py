from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import Societe, Utilisateur


class RegisterAndActivationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.email_sent_url = reverse("accounts:email_sent")

    def test_register_individual_user_sends_activation_email(self):
        """✅ Test qu’un utilisateur individuel peut s’inscrire et reçoit un email d’activation."""
        data = {
            "username": "brice",
            "email": "brice@example.com",
            "password1": "Motdepasse123!",
            "password2": "Motdepasse123!",
            "is_company": False,
            # Champs requis supplémentaires
            "first_name": "Brice",
            "last_name": "Yakpa",
            "individual_category": "agriculteur",  # adapte selon ton form field
        }

        response = self.client.post(self.register_url, data)

        # Vérifie que la vue redirige bien vers la page de confirmation
        self.assertRedirects(response, self.email_sent_url)

        user = Utilisateur.objects.get(username="brice")
        self.assertFalse(user.is_active)
        self.assertEqual(user.user_type, "individu")

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("Activez votre compte", email.subject)
        self.assertIn(user.email, email.to)

    def test_register_company_creates_societe(self):
        """✅ Test qu’un utilisateur entreprise crée aussi un objet Société lié."""
        data = {
            "username": "entrepriseuser",
            "email": "entreprise@example.com",
            "password1": "Motdepasse123!",
            "password2": "Motdepasse123!",
            "is_company": "on",
            # Champs supplémentaires du formulaire utilisateur
            "first_name": "Directeur",
            "last_name": "Entreprise",
            # Champs obligatoires du formulaire société
            "nom": "Société Test",
            "secteur": "Agroalimentaire",
            "company_type": "producteur",  # adapte au champ de ton modèle
        }

        response = self.client.post(self.register_url, data)

        self.assertRedirects(response, self.email_sent_url)

        user = Utilisateur.objects.get(username="entrepriseuser")
        self.assertEqual(user.user_type, "entreprise")
        self.assertFalse(user.is_active)

        societe = Societe.objects.get(utilisateur=user)
        self.assertEqual(societe.nom, "Société Test")

    def test_activation_with_valid_token_activates_user(self):
        """✅ Test qu’un token valide active le compte utilisateur."""
        user = Utilisateur.objects.create_user(
            username="brice",
            email="brice@example.com",
            password="Motdepasse123!",
            is_active=False,
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        activation_url = reverse("accounts:activate", args=[uid, token])
        response = self.client.get(activation_url, follow=True)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertRedirects(response, f"{self.login_url}?activated=1")

    def test_activation_with_invalid_token_fails(self):
        """❌ Test qu’un token invalide affiche la page d’erreur."""
        user = Utilisateur.objects.create_user(
            username="brice",
            email="brice@example.com",
            password="Motdepasse123!",
            is_active=False,
        )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_token = "mauvais_token"

        activation_url = reverse("accounts:activate", args=[uid, invalid_token])
        response = self.client.get(activation_url)

        self.assertTemplateUsed(response, "accounts/activation_invalid.html")
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_email_sent_view_renders_properly(self):
        """✅ Test que la page 'email envoyé' s’affiche correctement."""
        response = self.client.get(self.email_sent_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/emails.html")
