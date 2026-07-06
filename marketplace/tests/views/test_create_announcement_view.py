from io import BytesIO
from urllib.parse import parse_qs, urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from marketplace.forms import AnnouncementForm
from marketplace.models import Announcement, AnnouncementType
from marketplace.tests.views.base import MarketplaceViewTestCase


class CreateAnnouncementViewTests(MarketplaceViewTestCase):
    """
    Tests pour la vue CreateAnnouncementView qui permet de créer des annonces.
    Vérifie le comportement pour :
    - L'accès authentifié
    - La validation des catégories
    - La soumission du formulaire
    - La création effective d'annonces
    """

    def setUp(self):
        """
        Initialisation avant chaque test :
        - Crée un utilisateur connecté
        - Génère l'URL de création d'annonce
        """
        super().setUp()
        self.client.force_login(self.user)
        self.url = reverse(
            "marketplace:create_announcement",
            args=[self.category.id, self.subcategory.id],
        )

    def test_get_returns_200(self):
        """
        Test que la page de création renvoie bien un code 200 (OK)
        et contient le formulaire attendu.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], AnnouncementForm)

    def test_invalid_category_returns_404(self):
        """
        Test qu'une requête avec des IDs de catégorie invalides
        renvoie bien une erreur 404 (Not Found).
        """
        response = self.client.get(
            reverse("marketplace:create_announcement", args=[999, 999])
        )
        self.assertEqual(response.status_code, 404)

    def test_valid_post_creates_announcement(self):
        """
        Test qu'une soumission valide du formulaire :
        - Redirige (code 302)
        - Crée bien une nouvelle annonce en base
        """
        initial_count = Announcement.objects.count()
        data = {
            "title": "Nouvelle annonce vente",
            "type": AnnouncementType.SALE,
            "description": "Description de test",
            "product_name": "Produit test",
            "caracteristiques": "Caractéristiques test",
            "quantity": 10,
            "unit": "kg",
            "category": self.category.id,
            "subcategory": self.subcategory.id,
            "image": create_test_image(),  # <-- important
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Announcement.objects.count(), initial_count + 1)

    def test_unauthenticated_access_redirects(self):
        """
        Test qu'un utilisateur non connecté est redirigé vers la page de login
        avec le paramètre 'next' pour retourner à la création d'annonce après connexion.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))
        parsed = urlparse(response.url)
        query_params = parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/accounts/login/")
        self.assertIn("next", query_params)
        self.assertEqual(query_params["next"][0], self.url)


def create_test_image():
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.getvalue(), content_type="image/jpeg")
