# marketplace/cron_control.py

from django.core.management import call_command

from .models import CronTask


def update_crontabs():
    """
    Supprime les anciens cron et recrée seulement ceux activés
    """

    # 1️⃣ supprimer tous les cron existants
    call_command("crontab", "remove")

    # 2️⃣ ajouter les cron actifs
    active_tasks = CronTask.objects.filter(active=True)

    if active_tasks.exists():
        call_command("crontab", "add")

    # 3️⃣ afficher les cron (debug)
    call_command("crontab", "show")
