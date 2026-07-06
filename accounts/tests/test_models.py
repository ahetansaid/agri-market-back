import uuid

from accounts.models import Utilisateur


def create_unique_user(**kwargs):
    email = kwargs.get("email", f"user_{uuid.uuid4().hex[:8]}@example.com")
    username = kwargs.get("username", email.split("@")[0])
    password = kwargs.get("password", "password123")
    user = Utilisateur.objects.create(email=email, username=username)
    user.set_password(password)
    user.save()
    return user
