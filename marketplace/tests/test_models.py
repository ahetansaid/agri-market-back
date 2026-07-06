import os
import shutil
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from taggit.models import Tag

from accounts.models import Utilisateur
from marketplace.models import (
    Announcement,
    AnnouncementType,
    AnnouncementView,
    Category,
    SubCategory,
)

# Configuration pour les tests médias
TEST_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), "test_media")


def create_default_test_image(media_root):
    """
    Crée automatiquement default-product.jpg pour les tests
    """
    path = os.path.join(media_root, "announcements")
    os.makedirs(path, exist_ok=True)

    img_path = os.path.join(path, "default-product.jpg")

    if not os.path.exists(img_path):
        img = Image.new("RGB", (450, 450), color=(200, 200, 200))
        img.save(img_path, "JPEG")


def create_test_image():
    # Crée une image temporaire 100x100 pixels
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TestAnnouncementModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_default_test_image(TEST_MEDIA_ROOT)

    def setUp(self):
        # Données de base
        self.user = Utilisateur.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            pays="NE",  # Niger (pays africain)
        )

        # Création d'un second utilisateur pour les tests de validation
        self.validator1 = Utilisateur.objects.create_user(
            username="validator1",
            email="validator1@example.com",
            password="validatorpass123",
        )
        self.validator2 = Utilisateur.objects.create_user(
            username="validator2",
            email="validator2@example.com",
            password="validatorpass123",
        )

        # Groupes de validateurs
        self.first_validators_group = Group.objects.create(
            name="announcement_first_validators"
        )
        self.second_validators_group = Group.objects.create(
            name="announcement_second_validators"
        )
        self.first_validators_group.user_set.add(self.validator1)
        self.second_validators_group.user_set.add(self.validator2)

        # Catégories
        self.category = Category.objects.create(name="Fruits")
        self.subcategory = SubCategory.objects.create(name="Mangues")
        self.category.subcategories.add(self.subcategory)

        # Données communes pour les annonces
        self.announcement_data = {
            "title": "Vente de mangues",
            "description": "Mangues de qualité premium",
            "user": self.user,
            "category": self.category,
            "subcategory": self.subcategory,
            "country": "NE",
        }

    def create_test_image(self, size=(800, 600)):
        """Crée une image de test pour les tests"""
        image = Image.new("RGB", size, color=(255, 0, 0))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        return SimpleUploadedFile(
            "test_image.jpg", buffer.getvalue(), content_type="image/jpeg"
        )

    def test_announcement_creation(self):
        """Teste la création d'une annonce complète"""
        announcement = Announcement.objects.create(
            title="produit agricole",
            type=AnnouncementType.PURCHASE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="PURCHASE complet avec matériel moderne",
            country="NE",
            quantity=50,
            image=create_test_image(),
        )

        self.assertEqual(announcement.type, AnnouncementType.PURCHASE)
        self.assertEqual(announcement.user, self.user)
        self.assertEqual(announcement.status, "draft")  # Statut par défaut
        self.assertTrue(announcement.reference.startswith("REF-"))  # Référence générée

    def test_announcement_with_image(self):
        """Teste la création d'une annonce avec image"""
        # image_file = self.create_test_image()

        announcement = Announcement(
            title="Vente de mangues",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="Mangues de qualité",
            quantity=100,
            unit="kg",
            country="NE",
            product_name="product_name",
            image=create_test_image(),
        )
        announcement.full_clean()  # Teste la validation
        announcement.save()

        self.assertEqual(announcement.quantity, 100)
        self.assertEqual(announcement.unit, "kg")
        self.assertTrue(announcement.image.name.startswith("announcements/"))

    def test_required_fields_for_sale(self):
        """Teste que les champs quantité et unité sont requis pour les ventes"""
        announcement = Announcement(
            title="Vente sans quantité",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="Test",
            country="NE",
            quantity=50,
            image=create_test_image(),
        )

        with self.assertRaises(ValidationError):
            announcement.full_clean()  # Doit lever une ValidationError

    def test_announcement_str_method(self):
        """Teste la méthode __str__ de Announcement"""
        announcement = Announcement.objects.create(
            title="Location de tracteur",
            type=AnnouncementType.PURCHASE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="Tracteur 100CV avec chauffeur",
            country="NE",
            quantity=50,
            image=create_test_image(),
        )

        expected_str = f"{announcement.reference} - {announcement.title} - {announcement.get_type_display()}"
        self.assertEqual(str(announcement), expected_str)

    def test_publication_date(self):
        """Teste que la date de publication est automatique"""
        announcement = Announcement.objects.create(
            title="Test publication",
            type=AnnouncementType.PURCHASE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="Test",
            country="NE",
            status="approved",
            quantity=50,
            image=create_test_image(),
        )
        self.assertIsNotNone(announcement.publication_date)
        self.assertTrue(announcement.publication_date <= timezone.now())

    def test_valid_sale_announcement(self):
        """Teste qu'une annonce de vente valide passe la validation"""
        announcement = Announcement(
            title="Vente valide",
            type=AnnouncementType.SALE,
            user=self.user,
            category=self.category,
            subcategory=self.subcategory,
            description="Test",
            country="NE",
            quantity=100,
            unit="kg",
            product_name="product_name",
            image=create_test_image(),
        )

        try:
            announcement.full_clean()  # Ne doit pas lever d'exception
        except ValidationError:
            self.fail("La validation a échoué alors qu'elle aurait dû passer")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if os.path.exists(TEST_MEDIA_ROOT):
            shutil.rmtree(TEST_MEDIA_ROOT)

    def test_announcement_creation_minimal(self):
        """Teste la création minimale d'une annonce"""

        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=1,
            unit="kg",
        )

        self.assertEqual(announcement.type, AnnouncementType.PURCHASE)
        self.assertEqual(announcement.status, "draft")
        self.assertTrue(announcement.reference.startswith("REF-"))
        self.assertFalse(announcement.is_archived)
        self.assertEqual(announcement.image.name, "announcements/default-product.jpg")

    def test_announcement_full_creation(self):
        """Teste la création complète d'une annonce avec tous les champs"""
        # image = self.create_test_image()

        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.SALE,
            product_name="Mangues Kent",
            brand="Premium Fruits",
            variety="Kent",
            quantity=500,
            unit="kg",
            is_organic=True,
            shipping_conditions="Frais de port inclus",
            transaction_details="Paiement mobile accepté",
            restrictions="Pas d'export",
            image=create_test_image(),
        )
        announcement.tags.add("fruits", "bio", "afrique")

        # Vérification des champs de base
        self.assertEqual(announcement.type, AnnouncementType.SALE)
        self.assertEqual(announcement.product_name, "Mangues Kent")
        self.assertEqual(announcement.brand, "Premium Fruits")
        self.assertEqual(announcement.variety, "Kent")
        self.assertEqual(announcement.quantity, 500)
        self.assertEqual(announcement.unit, "kg")
        self.assertTrue(announcement.is_organic)
        self.assertEqual(announcement.shipping_conditions, "Frais de port inclus")
        self.assertEqual(announcement.transaction_details, "Paiement mobile accepté")
        self.assertEqual(announcement.restrictions, "Pas d'export")

        # Vérification des tags
        self.assertEqual(list(announcement.tags.names()), ["fruits", "bio", "afrique"])

        # Vérification de l'image
        self.assertTrue(announcement.image.name.startswith("announcements/"))
        self.assertTrue(os.path.exists(announcement.image.path))

    def test_announcement_str_representation(self):
        """Teste la représentation en string de l'annonce"""
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.SALE,
            product_name="Mangues",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        expected_str = f"{announcement.reference} - {announcement.title} - {announcement.get_type_display()}"

        self.assertEqual(str(announcement), expected_str)

    def test_get_absolute_url(self):
        """Teste la génération de l'URL absolue"""
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )

        expected_url = reverse(
            "marketplace:announcement_detail", args=[announcement.id]
        )
        self.assertEqual(announcement.get_absolute_url(), expected_url)

    def test_is_african_property(self):
        """Teste la propriété is_african"""
        # Pays africain
        data = {**self.announcement_data}
        del data["country"]  # Supprimez le country du dictionnaire de base

        announcement_africa = Announcement.objects.create(
            **data,
            type=AnnouncementType.PURCHASE,  # Ne passez le type qu'une seule fois
            country="NE",  # Niger
            product_name="Nom du produit",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )
        self.assertTrue(announcement_africa.is_african)

        # Pays non africain
        announcement_europe = Announcement.objects.create(
            **data,
            type=AnnouncementType.PURCHASE,
            country="FR",  # France
            product_name="Nom du produit",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )
        self.assertFalse(announcement_europe.is_african)

        # Pas de pays spécifié (doit utiliser le pays de l'utilisateur)
        announcement_no_country = Announcement.objects.create(
            **{k: v for k, v in self.announcement_data.items() if k != "country"},
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )
        self.assertTrue(announcement_no_country.is_african)

    def test_status_badges(self):
        """Teste les badges de statut"""
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=1,
            unit="kg",
            image=create_test_image(),
        )

        status_badge_map = {
            "draft": "secondary",
            "pending_first": "warning",
            "pending_second": "warning",
            "approved": "success",
            "rejected": "danger",
            "expired": "dark",
        }

        for status, expected_badge in status_badge_map.items():
            announcement.status = status
            announcement.save()
            self.assertEqual(announcement.get_status_badge, expected_badge)

    def test_image_validation(self):
        """Teste la validation des images"""
        # Image trop grande (>500KB)
        large_image = SimpleUploadedFile(
            "large.jpg", b"x" * 600 * 1024, content_type="image/jpeg"
        )

        announcement = Announcement(
            **self.announcement_data,
            type=AnnouncementType.SALE,
            product_name="Test",
            quantity=1,
            unit="kg",
            image=large_image,
        )

        with self.assertRaises(ValidationError):
            announcement.full_clean()

    def test_required_fields_for_sale_purchase(self):
        """Teste les champs obligatoires pour les annonces de vente/PURCHASE"""
        for ann_type in [AnnouncementType.SALE, AnnouncementType.PURCHASE]:
            # Données de base sans les champs requis
            data = {
                "title": "Test",
                "description": "Test",
                "user": self.user,
                "category": self.category,
                "subcategory": self.subcategory,
                "type": ann_type,
                "country": "NE",
            }

            # Test 1: Vérifie product_name
            with self.assertRaises(ValidationError) as cm:
                ann = Announcement(**data)
                ann.full_clean()
            errors = cm.exception.message_dict
            self.assertIn("product_name", errors)

            # Test 2: Vérifie quantity (avec product_name fourni)
            with self.assertRaises(ValidationError) as cm:
                ann = Announcement(**data, product_name="Produit test")
                ann.full_clean()
            errors = cm.exception.message_dict
            self.assertIn("quantity", errors)

            # Test 3: Vérifie unit (avec product_name et quantity fournis)
            with self.assertRaises(ValidationError) as cm:
                ann = Announcement(**data, product_name="Produit test", quantity=10)
                ann.full_clean()
            errors = cm.exception.message_dict
            self.assertIn("unit", errors)

            # Test 4: Tous les champs fournis - ne doit pas lever d'exception
            try:
                ann = Announcement(
                    **data, product_name="Produit test", quantity=10, unit="kg"
                )
                ann.full_clean()
            except ValidationError:
                self.fail("La validation a échoué alors qu'elle aurait dû passer")

    def test_validation_workflow(self):
        """Teste le workflow complet de validation"""
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=10,
            status="pending_first",
            image=create_test_image(),
        )
        self.assertEqual(announcement.status, "pending_first")

        # 2. Première approbation
        announcement.approve_first(self.validator1)
        self.assertEqual(announcement.status, "pending_second")
        self.assertEqual(announcement.first_approver, self.validator1)
        self.assertIsNotNone(announcement.first_approval_date)

        # 3. Seconde approbation
        announcement.approve_second(self.validator2)
        self.assertEqual(announcement.status, "approved")
        self.assertEqual(announcement.second_approver, self.validator2)
        self.assertIsNotNone(announcement.second_approval_date)
        self.assertIsNotNone(announcement.publication_date)

    def test_rejection_workflow(self):
        """Teste le workflow de rejet"""
        # Test rejet première validation
        announcement_pending_first = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            status="pending_first",
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        reason = "Contenu inapproprié"
        announcement_pending_first.reject(self.validator1, reason)

        self.assertEqual(announcement_pending_first.status, "rejected")
        self.assertEqual(announcement_pending_first.rejection_reason, reason)
        self.assertEqual(announcement_pending_first.first_approver, self.validator1)
        self.assertIsNone(announcement_pending_first.second_approver)

        # Test rejet seconde validation
        announcement_pending_second = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            status="pending_second",
            first_approver=self.validator1,
            first_approval_date=timezone.now(),
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        announcement_pending_second.reject(self.validator2, reason)

        self.assertEqual(announcement_pending_second.status, "rejected")
        self.assertEqual(announcement_pending_second.second_approver, self.validator2)
        self.assertIsNotNone(announcement_pending_second.second_approval_date)

    @patch("marketplace.models.send_mail")
    def test_notifications(self, mock_send_mail):
        """Teste l'envoi des notifications"""
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        # Test notification des validateurs
        announcement._notify_validators("first")
        self.assertTrue(mock_send_mail.called)

        # Réinitialise le mock pour le test suivant
        mock_send_mail.reset_mock()

        # Test notification du créateur
        announcement._notify_creator("Test message")
        self.assertTrue(mock_send_mail.called)

    def test_archiving(self):
        """Teste l'archivage des annonces"""
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        self.assertFalse(announcement.is_archived)

        announcement.is_archived = True
        announcement.save()

        self.assertTrue(announcement.is_archived)
        self.assertTrue(Announcement.objects.filter(is_archived=True).exists())

    def test_default_country_from_user(self):
        """Teste que le pays par défaut vient de l'utilisateur"""
        announcement = Announcement.objects.create(
            **{k: v for k, v in self.announcement_data.items() if k != "country"},
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        self.assertEqual(announcement.country, self.user.pays)

    def test_tags_management(self):
        """Teste la gestion des tags"""
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        announcement.tags.add("agriculture", "bio", "afrique")
        self.assertEqual(announcement.tags.count(), 3)

        # Vérifie que les tags existent bien en base
        self.assertTrue(
            Tag.objects.filter(name__in=["agriculture", "bio", "afrique"]).exists()
        )

    def test_auto_reference_generation(self):
        """Teste la génération automatique de la référence"""
        # Sans référence
        announcement = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            reference="",
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        self.assertTrue(announcement.reference.startswith("REF-"))
        self.assertEqual(len(announcement.reference), 14)  # REF- + 10 caractères

        # Avec référence existante
        original_ref = "REF-TEST12345"
        announcement2 = Announcement.objects.create(
            **self.announcement_data,
            type=AnnouncementType.PURCHASE,
            reference=original_ref,
            product_name="Nom du produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

        self.assertEqual(announcement2.reference, original_ref)


class TestAnnouncementViewModel(TestCase):
    """Tests pour le modèle AnnouncementView"""

    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

        category = Category.objects.create(name="Fruits")
        subcategory = SubCategory.objects.create(name="Mangues")

        self.announcement = Announcement.objects.create(
            title="Test View",
            type=AnnouncementType.PURCHASE,
            user=self.user,
            category=category,
            subcategory=subcategory,
            description="Test",
            country="NE",
            product_name="Nom produit",
            quantity=10,
            unit="kg",
            image=create_test_image(),
        )

    def test_view_creation(self):
        """Teste la création d'une vue"""
        view = AnnouncementView.objects.create(
            announcement=self.announcement,
            user=self.user,
            ip_address="127.0.0.1",
            session_key="testsessionkey",
        )

        self.assertEqual(view.announcement, self.announcement)
        self.assertEqual(view.user, self.user)
        self.assertEqual(view.ip_address, "127.0.0.1")
        self.assertEqual(view.session_key, "testsessionkey")
        self.assertIsNotNone(view.created_at)

    def test_unique_view_constraint(self):
        """Teste la contrainte d'unicité des vues"""
        # Première vue
        AnnouncementView.objects.create(
            announcement=self.announcement,
            ip_address="127.0.0.1",
            session_key="testsessionkey",
        )

        # Deuxième vue identique
        with self.assertRaises(Exception) as context:
            AnnouncementView.objects.create(
                announcement=self.announcement,
                ip_address="127.0.0.1",
                session_key="testsessionkey",
                test_mode=True,
            )

        # Vérifie qu'une exception a bien été levée (peut être IntegrityError ou autre)
        self.assertTrue(context.exception)

        # Vue différente (IP différente) devrait passer
        AnnouncementView.objects.create(
            announcement=self.announcement,
            ip_address="192.168.1.1",
            session_key="testsessionkey",
        )
        self.assertEqual(AnnouncementView.objects.count(), 2)

        def test_view_str_representation(self):
            """Teste la représentation en string d'une vue"""
            view = AnnouncementView.objects.create(
                announcement=self.announcement,
                ip_address="127.0.0.1",
            )

            self.assertEqual(str(view), f"Vue de {self.announcement.title}")


class TestCategoryModels(TestCase):
    """Tests pour les modèles Category et SubCategory"""

    def setUp(self):
        self.category = Category.objects.create(name="Fruits")
        self.subcategory1 = SubCategory.objects.create(name="Mangues")
        self.subcategory2 = SubCategory.objects.create(name="Bananes")

    def test_category_creation(self):
        """Teste la création d'une catégorie"""
        self.assertEqual(self.category.name, "Fruits")
        self.assertEqual(str(self.category), "Fruits")
        self.assertEqual(self.category.subcategories.count(), 0)

        # Ajout de sous-catégories
        self.category.subcategories.add(self.subcategory1, self.subcategory2)
        self.assertEqual(self.category.subcategories.count(), 2)

        # Vérification du tri
        categories = Category.objects.all()
        self.assertEqual(categories[0].name, "Fruits")

    def test_subcategory_creation(self):
        """Teste la création d'une sous-catégorie"""
        self.assertEqual(self.subcategory1.name, "Mangues")
        self.assertEqual(str(self.subcategory1), "Mangues")

        # Vérification du tri
        subcategories = SubCategory.objects.all().order_by("name")
        self.assertEqual(subcategories[0].name, "Bananes")  # Tri alphabétique
        self.assertEqual(subcategories[1].name, "Mangues")
