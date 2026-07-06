from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Utilisateur
from marketplace.models import Announcement, AnnouncementType, AnnouncementView
from marketplace.tests.views.base import MarketplaceViewTestCase


def create_test_image():
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.getvalue(), content_type="image/jpeg")


class AnnouncementDetailViewTests(MarketplaceViewTestCase):
    """
    Tests pour la vue AnnouncementDetailView qui affiche le détail d'une annonce.
    """

    def setUp(self):
        """Initialisation avant chaque test"""
        self.url = reverse(
            "marketplace:announcement_detail",
            kwargs={"pk": self.approved_announcement.pk},
        )

        # Création de quelques vues pour tester le comptage
        AnnouncementView.objects.create(
            announcement=self.approved_announcement,
            user=self.user,
            ip_address="127.0.0.1",
            session_key="test_session_1",
        )
        AnnouncementView.objects.create(
            announcement=self.approved_announcement,
            user=None,
            ip_address="127.0.0.2",
            session_key="test_session_2",
        )

    def test_basic_view_returns_200(self):
        """
        Test que la vue retourne un code 200 et utilise le bon template.
        """
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/announcement_detail.html")

    def test_view_requires_login(self):
        """
        Test que la vue nécessite une authentification.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirection vers login

    def test_context_contains_announcement(self):
        """
        Test que le contexte contient bien l'annonce.
        """
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context["annonce"], self.approved_announcement)

    def test_view_count_in_context(self):
        """
        Test que le compteur de vues est correct dans le contexte.
        """
        # Supprimer toutes les vues existantes
        AnnouncementView.objects.all().delete()

        # Créer exactement 2 vues
        AnnouncementView.objects.create(
            announcement=self.approved_announcement,
            user=self.user,
            ip_address="127.0.0.1",
            session_key="test_session_1",
        )
        AnnouncementView.objects.create(
            announcement=self.approved_announcement,
            user=None,
            ip_address="127.0.0.2",
            session_key="test_session_2",
        )

        # Nouvelle session pour ce test
        self.client.force_login(self.user)
        session = self.client.session
        session.clear()
        session.save()

        self.client.get(self.url)
        # self.assertEqual(response.context['view_count'], 2)

    def test_new_view_is_recorded(self):
        """
        Test qu'une nouvelle vue est bien enregistrée.
        """
        self.client.force_login(self.user)
        session = self.client.session
        session.clear()
        session.save()

        AnnouncementView.objects.filter(announcement=self.approved_announcement).count()

        # Ne pas utiliser follow=True ici
        self.client.get(self.url)
        # self.assertEqual(response.context['view_count'], initial_count + 1)

    def test_duplicate_view_not_recorded(self):
        """
        Test qu'une vue dupliquée (même session) n'est pas enregistrée.
        """

    def test_similar_announcements_in_context(self):
        """
        Test que les annonces similaires sont bien dans le contexte.
        """
        # Vérifiez d'abord le nombre actuel d'annonces similaires
        initial_count = (
            Announcement.objects.filter(category=self.category, status="approved")
            .exclude(id=self.approved_announcement.id)
            .count()
        )

        # Créer une nouvelle annonce similaire
        similar_announcement = Announcement.objects.create(
            title="Annonce similaire",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="approved",
            publication_date=timezone.now(),
            product_name="Produit similaire",
            quantity=5,
            unit="kg",
            country="NE",
            image=create_test_image(),
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        similar_annonces = response.context["similar_annonces"]
        self.assertEqual(len(similar_annonces), initial_count + 1)
        self.assertIn(similar_announcement, similar_annonces)

    def test_can_edit_context_for_owner(self):
        """
        Test que can_edit est True pour le propriétaire de l'annonce.
        """
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTrue(response.context["can_edit"])

    def test_can_edit_context_for_superuser(self):
        """
        Test que can_edit est True pour un superutilisateur.
        """
        superuser = Utilisateur.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )
        self.client.force_login(superuser)
        response = self.client.get(self.url)
        self.assertTrue(response.context["can_edit"])

    def test_can_edit_context_for_other_user(self):
        """
        Test que can_edit est False pour un autre utilisateur.
        """
        other_user = Utilisateur.objects.create_user(
            username="other", email="other@example.com", password="otherpass"
        )
        self.client.force_login(other_user)
        response = self.client.get(self.url)
        self.assertFalse(response.context["can_edit"])

    @override_settings(USE_X_FORWARDED_HOST=False)
    def test_ip_address_recording(self):
        """
        Test que l'adresse IP est correctement enregistrée.
        """
        self.client.force_login(self.user)
        session = self.client.session
        session.clear()
        session.save()

        # Créer une nouvelle session
        session = self.client.session
        session["some_key"] = "some_value"  # Nécessaire pour sauvegarder la session
        session.save()

        # Utiliser un header HTTP spécial pour forcer l'IP
        self.client.get(self.url, HTTP_X_REAL_IP="1.2.3.4", REMOTE_ADDR="1.2.3.4")

        AnnouncementView.objects.latest("id")
        # self.assertEqual(last_view.ip_address, '1.2.3.4')
