"""Crée OU met à jour un compte admin (staff + superuser) de façon idempotente.

Contrairement à `createsuperuser --noinput` (qui échoue si le username existe
déjà et ne met jamais à jour le mot de passe), cette commande :
  - crée le compte s'il n'existe pas ;
  - sinon met à jour son mot de passe et le promeut staff + superuser + actif.

Utile sur Render free tier (pas de Shell) : elle tourne au build.

Source des identifiants (par ordre de priorité) :
  1. options CLI : --username --email --password
  2. variables d'environnement : DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée ou met à jour un compte admin (staff+superuser) idempotent."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=None)
        parser.add_argument("--email", default=None)
        parser.add_argument("--password", default=None)

    def handle(self, *args, **opts):
        User = get_user_model()

        username = opts["username"] or os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = opts["email"] or os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = opts["password"] or os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                "promote_staff: DJANGO_SUPERUSER_USERNAME/PASSWORD absents — ignoré."
            )
            return

        user = User.objects.filter(username=username).first()
        if user is None and email:
            user = User.objects.filter(email__iexact=email).first()

        created = user is None
        if created:
            user = User(username=username, email=email or "")
        elif email:
            user.email = email

        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = "Créé" if created else "Mis à jour"
        self.stdout.write(
            self.style.SUCCESS(
                f"promote_staff: {action} — {user.username} "
                f"(staff+superuser, mot de passe défini)."
            )
        )
