# from django.views.decorators.cache import cache_page, never_cache
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView,
    TemplateView,
    View,
)

from accounts.models import Utilisateur
from marketplace.models import Announcement

from .models import About, Conversation, Message, Presentation


class AboutView(View):
    template_name = "blog/abouts.html"

    def get(self, request, *args, **kwargs):
        abouts = list(About.objects.filter(archive=True))

        # Groupage par mots-cles dans le titre pour des layouts dedies
        def find(*keywords):
            for a in abouts:
                t = (a.title or "").lower()
                if any(k in t for k in keywords):
                    return a
            return None

        intro = find("a propos", "à propos", "propos de", "agri market")
        vision = find("vision")
        mission = find("mission")
        perspective = find("perspective", "avenir", "futur")

        used_ids = {x.id for x in (intro, vision, mission, perspective) if x}
        values = [a for a in abouts if a.id not in used_ids and a.title]

        context = {
            "abouts": abouts,  # garde la liste complete pour le fallback
            "about_intro": intro,
            "about_vision": vision,
            "about_mission": mission,
            "about_perspective": perspective,
            "about_values": values,
            "has_grouped": bool(intro or vision or mission or perspective or values),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        return HttpResponse("POST request!")


class PresentationView(View):
    template_name = "blog/presentation.html"

    def get(self, request, *args, **kwargs):
        from .models import Partenaire, Sponsor

        presentation = Presentation.objects.filter(archive=True).first()
        all_presentations = list(Presentation.objects.filter(archive=True))

        context = {
            "presentation": presentation,
            "presentations": all_presentations,
            "partenaires": Partenaire.objects.filter(archive=False),
            "sponsors": Sponsor.objects.filter(archive=False),
        }
        return render(request, self.template_name, context)


class InboxView(ListView):
    template_name = "blog/inbox.html"
    context_object_name = "conversations"

    def get_queryset(self):
        queryset = Conversation.objects.filter(
            seller=self.request.user, archive=False
        ).order_by("-started_at")
        for conv in queryset:
            conv.unread_count = (
                conv.messages.filter(is_read=False, archive=False)
                .exclude(sender=self.request.user)
                .count()
            )
        return queryset


class SentView(ListView):
    template_name = "blog/sent.html"
    context_object_name = "conversations"

    def get_queryset(self):
        return (
            Conversation.objects.filter(buyer=self.request.user, archive=False)
            .annotate(
                unread_count=Count(
                    "messages",
                    filter=Q(messages__is_read=False)
                    & ~Q(messages__sender=self.request.user),
                )
            )
            .order_by("-started_at")
        )


@login_required
def restore_conversation(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    if conversation.buyer != request.user and conversation.seller != request.user:
        messages.error(
            request, "Vous n'avez pas le droit de restaurer cette conversation."
        )
        return redirect("blog:trash")

    conversation.archive = False
    conversation.save()
    messages.success(request, "Conversation restaurée avec succès.")
    return redirect("blog:inbox")


class TrashView(ListView):
    template_name = "blog/trash.html"
    context_object_name = "conversations"

    def get_queryset(self):
        conversations = Conversation.objects.filter(archive=True).filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user)
        )

        # Injecter une propriété "other_user" dans chaque conversation
        for conv in conversations:
            conv.other_user = (
                conv.seller if conv.buyer == self.request.user else conv.buyer
            )
        return conversations


@login_required
def archive_conversation(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    # 💡 Vérifie si l'utilisateur est concerné
    if conversation.buyer != request.user and conversation.seller != request.user:
        messages.error(
            request, "Vous n'avez pas le droit de supprimer cette conversation."
        )
        return redirect("blog:inbox")

    # Mettre à jour uniquement pour l'utilisateur connecté
    conversation.archive = True
    conversation.save()
    messages.success(request, "Conversation déplacée dans la corbeille.")
    return redirect("blog:inbox")  # ou autre nom


@method_decorator(login_required, name="dispatch")
class ConversationDetailView(View):

    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        if request.user != conversation.buyer and request.user != conversation.seller:
            return redirect("/")

        messages = conversation.messages.all()
        for msg in messages.filter(is_read=False).exclude(sender=request.user):
            msg.is_read = True
            msg.save()

        return render(
            request,
            "blog/conversation_detail.html",
            {
                "conversation": conversation,
                "messages": messages,
            },
        )

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)

        if request.user != conversation.buyer and request.user != conversation.seller:
            return redirect("/")

        content = request.POST.get("content")
        attachment = request.FILES.get("attachment")
        image = request.FILES.get("image")

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            attachment=attachment,
            image=image,
        )

        # 🔥 Déterminer le destinataire
        if request.user == conversation.buyer:
            recipient = conversation.seller
        else:
            recipient = conversation.buyer

        #  Infos du site
        current_site = Site.objects.get_current()
        domain = current_site.domain
        protocol = "https"

        #  Contexte email
        context = {
            "sender": request.user,
            "recipient": recipient,
            "conversation": conversation,
            "message": message,
            "domain": domain,
            "protocol": protocol,
        }

        #  Email
        subject = "Nouveau message concernant votre annonce"
        email_message = render_to_string(
            "blog/emails/new_message_notification.txt",
            context,
        )

        send_mail(
            subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
            fail_silently=True,
        )

        # 🔥 Récupérer les admins
        admins = Utilisateur.objects.filter(is_superuser=True).exclude(email="")

        admin_emails = [admin.email for admin in admins if admin.email]

        if admin_emails:
            admin_subject = " ADMIN Nouveau message dans une conversation"

            admin_context = {
                "sender": request.user,
                "recipient": recipient,
                "conversation": conversation,
                "message": message,
                "domain": domain,
                "protocol": protocol,
            }

            admin_email_message = render_to_string(
                "blog/emails/admin_new_message_notification.txt",
                admin_context,
            )

            send_mail(
                admin_subject,
                admin_email_message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True,
            )

        return redirect("blog:conversations", pk=conversation.pk)


@method_decorator(login_required, name="dispatch")
class StartConversationView(View):
    def get(self, request, announcement_id):
        announcement = get_object_or_404(Announcement, id=announcement_id)
        buyer = request.user
        seller = announcement.user

        if buyer == seller:
            return redirect("marketplace:announcement_detail", pk=announcement.id)

        conversation, created = Conversation.objects.get_or_create(
            announcement=announcement, buyer=buyer, seller=seller
        )

        return redirect("blog:conversations", pk=conversation.pk)


class FaqView(TemplateView):
    """Page FAQ — questions/reponses statiques, accordeon Alpine.js."""

    template_name = "blog/faq.html"


class GuideView(TemplateView):
    """Guide utilisateur — tutoriel pas-a-pas pour bien commencer."""

    template_name = "blog/guide.html"
