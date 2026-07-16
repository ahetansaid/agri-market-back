# marketplace/cron_control.py

import logging

from django.core.management import call_command

from .models import CronTask

logger = logging.getLogger(__name__)


def update_crontabs():
    """
    Supprime les anciens cron et recrée seulement ceux activés.

    Best-effort : sur les environnements sans démon cron (Render, Windows),
    la commande `crontab` échoue — cela ne doit JAMAIS faire planter
    l'enregistrement d'un CronTask dans l'admin.
    """
    try:
        # 1️⃣ supprimer tous les cron existants
        call_command("crontab", "remove")

        # 2️⃣ ajouter les cron actifs
        active_tasks = CronTask.objects.filter(active=True)
        if active_tasks.exists():
            call_command("crontab", "add")

        # 3️⃣ afficher les cron (debug)
        call_command("crontab", "show")
    except Exception:
        logger.exception(
            "Mise a jour du crontab impossible sur cet environnement "
            "(pas de demon cron ?) — enregistrement CronTask conserve."
        )
