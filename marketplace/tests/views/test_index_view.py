from django.urls import reverse

from marketplace.models import Announcement
from marketplace.tests.views.base import MarketplaceViewTestCase


class IndexViewTests(MarketplaceViewTestCase):
    """
    Tests pour l'IndexView qui affiche la page d'accueil de la place de marché.

    Cette vue doit :
    - renvoyer un code d'état HTTP 200
    - Afficher uniquement les annonces approuvées
    - afficher le bon modèle
    - Gérer les cas où aucune annonce n'est disponible
    """

    def test_index_view_returns_200(self):
        """
        Testez que la vue d'index renvoie un code d'état HTTP 200
        et utilise le bon modèle.
        """
        response = self.client.get(reverse("marketplace:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "marketplace/index.html")

    def test_index_shows_approved_announcements(self):
        """
        Testez que la vue de l'index n'affiche que les annonces approuvées
        et filtre les annonces en attente.
        """
        response = self.client.get(reverse("marketplace:index"))

        # Verify approved announcement is shown
        self.assertContains(response, self.approved_announcement.title)

        # Verify pending announcement is not shown
        self.assertNotContains(response, self.pending_first_announcement.title)

    def test_index_with_no_approved_announcements(self):
        """
        Testez l'affichage de l'index lorsqu'il n'y a pas d'annonces approuvées.
        L'affichage devrait toujours renvoyer 200, mais avec des résultats vides.
        """
        # Set all announcements to draft status
        Announcement.objects.update(status="draft")

        response = self.client.get(reverse("marketplace:index"))

        # Verify the announcements list is empty
        self.assertEqual(len(response.context["annonces"]), 0)
