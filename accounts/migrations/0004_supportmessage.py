import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_sellerrating"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("body", models.TextField(verbose_name="Message")),
                (
                    "from_staff",
                    models.BooleanField(
                        default=False, verbose_name="Réponse du service client"
                    ),
                ),
                (
                    "is_read",
                    models.BooleanField(
                        default=False, verbose_name="Lu par le destinataire"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="support_messages",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Message support",
                "verbose_name_plural": "Messages support",
                "ordering": ["created_at"],
            },
        ),
    ]
