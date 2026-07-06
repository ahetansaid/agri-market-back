from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import Utilisateur
from blog.models import About
from marketplace.models import Announcement, Category, SubCategory

from .models import Conversation, Message


def create_test_image():
    image = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.getvalue(), content_type="image/jpeg")


class MessagingTests(TestCase):
    def setUp(self):
        self.seller = Utilisateur.objects.create_user(
            username="seller", email="seller@example.com", password="testpass"
        )

        self.buyer = Utilisateur.objects.create_user(
            username="buyer", email="buyer@example.com", password="testpass"
        )

        # ✅ Ajouter aussi category et subcategory si c'est obligatoire
        category = Category.objects.create(name="Matériel agricole")
        subcategory = SubCategory.objects.create(name="Tracteurs", category=category)

        self.announcement = Announcement.objects.create(
            reference="REF-1234",
            title="Location de tracteur",
            type="Achat",
            user=self.seller,
            category=category,  # ✅ obligatoire
            subcategory=subcategory,  # ✅ obligatoire
            image=create_test_image(),  # ← ajouté pour le test
            caracteristiques="Caractéristiques test",  # si nécessaire
        )

        self.conversation = Conversation.objects.create(
            announcement=self.announcement,
            seller=self.seller,
            buyer=self.buyer,  # ✅ obligatoire
        )

        # Création d'un message "Hello"
        self.message = Message.objects.create(
            conversation=self.conversation, sender=self.seller, content="Hello"
        )

    def test_about_view(self):
        About.objects.create(title="About 1", archive=True)
        response = self.client.get(reverse("blog:abouts"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About 1")

    # def test_inbox_view_authenticated(self):
    #     self.client.login(username="seller", password="testpass")
    #     response = self.client.get(reverse("blog:inbox"))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Hello")

    def test_inbox_view_authenticated(self):
        self.client.login(username="seller", password="testpass")
        url = reverse("blog:inbox")
        response = self.client.get(url)

        # Vérifier que la page contient le nom de l’acheteur et le titre de l’annonce
        self.assertContains(response, self.buyer.username)
        self.assertContains(response, self.announcement.title)

    def test_sent_view_authenticated(self):
        self.client.login(username="buyer", password="testpass")
        response = self.client.get(reverse("blog:sent"))
        self.assertEqual(response.status_code, 200)

    def test_archive_and_restore_conversation(self):
        self.client.login(username="buyer", password="testpass")
        archive_url = reverse("blog:archive_conversation", args=[self.conversation.pk])
        restore_url = reverse("blog:restore_conversation", args=[self.conversation.pk])

        # Archive
        response = self.client.get(archive_url)
        self.assertRedirects(response, reverse("blog:inbox"))
        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.archive)

        # Restore
        response = self.client.get(restore_url)
        self.assertRedirects(response, reverse("blog:inbox"))
        self.conversation.refresh_from_db()
        self.assertFalse(self.conversation.archive)

    def test_trash_view(self):
        self.conversation.archive = True
        self.conversation.save()
        self.client.login(username="buyer", password="testpass")
        response = self.client.get(reverse("blog:trash"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.seller.username)

    def test_conversation_detail_view_get_and_post(self):
        self.client.login(username="buyer", password="testpass")
        url = reverse("blog:conversations", args=[self.conversation.pk])

        # GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello")

        # POST
        response = self.client.post(url, {"content": "Reply"})
        self.assertRedirects(response, url)
        self.assertTrue(Message.objects.filter(content="Reply").exists())

    def test_start_conversation_view(self):
        self.client.login(username="buyer", password="testpass")
        url = reverse("blog:start_conversation", args=[self.announcement.id])
        response = self.client.get(url)
        self.assertRedirects(
            response, reverse("blog:conversations", args=[self.conversation.pk])
        )
