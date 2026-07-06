import os
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from accounts.models import Utilisateur
from evenements.models import Evenement
from marketplace.models import Announcement, AnnouncementType, Category, SubCategory


@override_settings(MEDIA_ROOT=os.path.join(os.path.dirname(__file__), "test_media"))
class MarketplaceViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # -----------------------------
        # Création des utilisateurs
        # -----------------------------
        cls.user = Utilisateur.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        cls.validator1 = Utilisateur.objects.create_user(
            username="validator1",
            email="validator1@example.com",
            password="validatorpass123",
        )

        cls.validator2 = Utilisateur.objects.create_user(
            username="validator2",
            email="validator2@example.com",
            password="validatorpass123",
        )

        # Groupes de validation
        cls.first_validators = Group.objects.create(
            name="announcement_first_validators"
        )
        cls.second_validators = Group.objects.create(
            name="announcement_second_validators"
        )
        cls.first_validators.user_set.add(cls.validator1)
        cls.second_validators.user_set.add(cls.validator2)

        # -----------------------------
        # Catégories et sous-catégories
        # -----------------------------
        cls.category = Category.objects.create(name="Fruits")
        cls.subcategory = SubCategory.objects.create(name="Mangues")
        cls.category.subcategories.add(cls.subcategory)

        # -----------------------------
        # Annonces avec image générée en mémoire
        # -----------------------------
        cls.approved_announcement = Announcement.objects.create(
            title="Annonce approuvée",
            type=AnnouncementType.SALE,
            user=cls.user,
            category=cls.category,
            subcategory=cls.subcategory,
            status="approved",
            publication_date=timezone.now(),
            product_name="Produit test",
            quantity=10,
            unit="kg",
            country="NE",
            is_archived=False,
            image=cls.create_test_image(),
        )

        cls.pending_first_announcement = Announcement.objects.create(
            title="Annonce en attente première validation",
            type=AnnouncementType.PURCHASE,
            user=cls.user,
            category=cls.category,
            subcategory=cls.subcategory,
            status="pending_first",
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=cls.create_test_image(),
        )

        # -----------------------------
        # Événement de test
        # -----------------------------
        cls.event = Evenement.objects.create(
            slug="b2b-turin-2026",
            titre="B2B Turin 2026",
            est_actif=True,
            date_debut=timezone.now(),
            date_fin=timezone.now() + timezone.timedelta(days=20),
        )

    # -----------------------------
    # Nettoyage des fichiers MEDIA
    # -----------------------------
    def tearDown(self):
        if os.path.exists(settings.MEDIA_ROOT):
            for root, dirs, files in os.walk(settings.MEDIA_ROOT, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(settings.MEDIA_ROOT)

    # -----------------------------
    # Création d'une image de test en mémoire
    # -----------------------------
    @classmethod
    def create_test_image(cls):
        image = Image.new("RGB", (100, 100), color=(73, 109, 137))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        return SimpleUploadedFile(
            "test.jpg", buffer.getvalue(), content_type="image/jpeg"
        )

    # -----------------------------
    # Méthode utilitaire pour les messages
    # -----------------------------
    def assert_message_exists(self, response, expected_message):
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(expected_message in str(message) for message in messages),
            f"Message attendu non trouvé : {expected_message}",
        )
