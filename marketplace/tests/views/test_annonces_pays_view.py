from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from django_countries import countries
from PIL import Image

from marketplace.models import Announcement, AnnouncementType
from marketplace.tests.views.base import MarketplaceViewTestCase


def create_test_image():
    # Crée une image temporaire 100x100 pixels
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.getvalue(), content_type="image/jpeg")


class AnnoncesPaysViewTests(MarketplaceViewTestCase):
    """
    Tests pour la vue AnnoncesPays qui affiche les annonces par pays.
    """

    def setUp(self):
        super().setUp()  # si nécessaire pour initialiser les données de base
        self.country_code = "NE"  # Niger
        self.country_name = countries.name(self.country_code)
        self.url = reverse("marketplace:paysproduit", args=[self.country_code])

        # Annonce dans le pays testé (Niger)
        self.other_announcement = Announcement.objects.create(
            title="Service agricole au Niger",
            type=AnnouncementType.OTHER,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="approved",
            publication_date=timezone.now(),
            country=self.country_code,
            description="Service de test au Niger",
            product_name="Produit similaire",
            quantity=5,
            unit="kg",
            image=create_test_image(),
        )

        # 🔹 Annonce dans un autre pays (par ex. Togo)
        self.other_country_announcement = Announcement.objects.create(
            title="Service agricole au Togo",
            type=AnnouncementType.OTHER,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="approved",
            publication_date=timezone.now(),
            country="TG",  # Togo
            description="Service de test au Togo",
            product_name="Produit étranger",
            quantity=3,
            unit="kg",
            image=create_test_image(),
        )

    def test_basic_view_returns_200(self):
        """
        Test que la vue retourne un code 200 et utilise le bon template.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/annonces_pays.html")

    def test_view_shows_only_country_announcements(self):
        """
        Test que seules les annonces du pays spécifié sont affichées.
        """
        response = self.client.get(self.url)

        # Vérifie que les annonces du pays sont présentes
        self.assertContains(response, self.approved_announcement.title)
        self.assertContains(response, self.other_announcement.title)

        # Vérifie que les annonces d'autres pays ne sont pas affichées
        self.assertNotContains(response, self.other_country_announcement.title)

    def test_view_context_contains_country_info(self):
        """
        Test que le contexte contient bien les informations du pays.
        """
        response = self.client.get(self.url)

        # Vérifie les éléments du contexte
        self.assertEqual(response.context["country_name"], self.country_name)
        self.assertEqual(response.context["country_code"], self.country_code)

    def test_pagination(self):
        """
        Test que la pagination fonctionne correctement.
        """
        # Création de plusieurs annonces pour le pays testé
        for i in range(15):
            Announcement.objects.create(
                title=f"Annonce test {i}",
                type=AnnouncementType.SALE,
                user=self.user,
                category=self.category,
                subcategory=self.subcategory,
                status="approved",
                publication_date=timezone.now(),
                country=self.country_code,
                product_name=f"Produit {i}",
                quantity=1,
                unit="unité",
                image=create_test_image(),
            )

        # Test avec le paramètre de pagination dans les query params
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(response.status_code, 200)

        # Vérifie que le contexte contient bien un paginator
        self.assertTrue("paginator" in response.context)
        self.assertTrue("page_obj" in response.context)

        # Vérifie qu'on a bien la deuxième page
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_invalid_country_returns_404(self):
        """
        Test qu'un code pays invalide retourne une 404.
        """
        # Test avec un code trop long
        invalid_url = reverse("marketplace:paysproduit", args=["INVALID"])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

        # Test avec un code trop court
        invalid_url = reverse("marketplace:paysproduit", args=["X"])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_only_approved_announcements_are_shown(self):
        """
        Test que seules les annonces approuvées sont affichées.
        """
        # Création d'une annonce non approuvée pour le même pays
        pending_announcement = Announcement.objects.create(
            title="Annonce en attente",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="pending_first",
            country=self.country_code,
            product_name="Produit en attente",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )

        response = self.client.get(self.url)
        self.assertNotContains(response, pending_announcement.title)

    def test_ordering_by_publication_date(self):
        """
        Test que les annonces sont bien ordonnées par date de publication décroissante.
        """
        # Création d'une nouvelle annonce plus récente
        new_announcement = Announcement.objects.create(
            title="Nouvelle annonce Niger",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="approved",
            publication_date=timezone.now(),
            country=self.country_code,
            product_name="Nouveau produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        response = self.client.get(self.url)
        announcements = list(response.context["annonces"])

        # La nouvelle annonce doit apparaître en premier
        self.assertEqual(announcements[0].title, new_announcement.title)
        self.assertEqual(announcements[1].title, self.other_announcement.title)
        self.assertEqual(announcements[2].title, self.approved_announcement.title)
