from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
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


class AllAnnouncementsListViewTests(MarketplaceViewTestCase):
    """
    Tests pour la vue AllAnnouncementsListView qui affiche toutes les annonces approuvées.
    Vérifie :
    - L'affichage de base sans filtres
    - Le filtrage par type d'annonce
    - La pagination
    - Le contexte template (catégories, types d'annonce)
    """

    def setUp(self):
        """Initialisation avant chaque test"""
        self.url = reverse("marketplace:all_announcements")

        # Annonce approuvée
        self.approved_announcement = Announcement.objects.create(
            title="Annonce approuvée",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="approved",
            is_archived=False,
            publication_date=timezone.now(),
            product_name="Produit A",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )

        # Annonce non approuvée
        self.pending_first_announcement = Announcement.objects.create(
            title="Annonce en attente",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="pending",
            is_archived=False,
            publication_date=timezone.now(),
            product_name="Produit B",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )

        # Autre annonce pour tester le filtre
        self.other_announcement = Announcement.objects.create(
            title="Annonce autre",
            type=AnnouncementType.OTHER,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="approved",
            is_archived=False,
            publication_date=timezone.now(),
            description="Annonce de type autre",
            product_name="Produit similaire",
            quantity=5,
            unit="kg",
            image=create_test_image(),
        )

    def test_basic_view_returns_200(self):
        """Test que la vue retourne un code 200 et utilise le bon template."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/all_announcements.html")

    def test_view_shows_approved_announcements(self):
        """Test que seules les annonces approuvées sont affichées."""
        response = self.client.get(self.url)

        # Vérifie que les annonces approuvées sont présentes
        self.assertContains(response, self.approved_announcement.title)
        self.assertContains(response, self.other_announcement.title)

        # Vérifie que les annonces non approuvées ne sont pas affichées
        self.assertNotContains(response, self.pending_first_announcement.title)

    def test_filter_by_announcement_type(self):
        """Test le filtrage des annonces par type (vente/autre)."""
        # Filtre par vente
        response = self.client.get(self.url, {"type": "vente"})
        self.assertEqual(response.status_code, 200)

        self.assertIn("annonces", response.context)
        sale_annonces = response.context["annonces"]
        self.assertTrue(
            any(a.title == self.approved_announcement.title for a in sale_annonces)
        )
        self.assertFalse(
            any(a.title == self.other_announcement.title for a in sale_annonces)
        )

        # Filtre par autre
        response = self.client.get(self.url, {"type": "autre"})
        self.assertEqual(response.status_code, 200)

        self.assertIn("annonces", response.context)
        other_annonces = response.context["annonces"]
        self.assertTrue(
            any(a.title == self.other_announcement.title for a in other_annonces)
        )
        self.assertFalse(
            any(a.title == self.approved_announcement.title for a in other_annonces)
        )

    def test_pagination(self):
        """Test que la pagination fonctionne correctement."""
        # Création de plusieurs annonces avec publication_date
        for i in range(50):
            Announcement.objects.create(
                title=f"Annonce test {i}",
                type=AnnouncementType.SALE,
                user=self.user,
                category=self.category,
                subcategory=self.subcategory,
                status="approved",
                publication_date=timezone.now(),
                product_name="Produit test",
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

    def test_template_context(self):
        """Test que le contexte contient bien les catégories et types d'annonce."""
        response = self.client.get(self.url)

        # Vérifie les éléments du contexte
        self.assertIn("categories", response.context)
        self.assertIn("announcement_types", response.context)

        # Vérifie que les catégories sont bien celles attendues
        self.assertEqual(list(response.context["categories"]), [self.category])

        # Vérifie que tous les types d'annonce sont présents
        self.assertEqual(
            len(response.context["announcement_types"]), len(AnnouncementType.choices)
        )

    def test_ordering(self):
        """Test que les annonces sont bien ordonnées par date de publication décroissante."""
        # Création d'une nouvelle annonce plus récente
        new_announcement = Announcement.objects.create(
            title="Nouvelle annonce",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            status="approved",
            publication_date=timezone.now(),
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
