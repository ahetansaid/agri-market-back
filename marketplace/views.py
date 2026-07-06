from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

# from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.cache import never_cache
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django_countries import countries

from blog.models import Partenaire, Slide, Sponsor
from evenements.models import Evenement

from .forms import AnnouncementForm
from .models import (
    Announcement,
    AnnouncementType,
    AnnouncementView,
    Category,
    SubCategory,
)


class SetLanguageView(View):
    def get(self, request, *args, **kwargs):
        app_name = request.GET.get("app_name")
        url_name = request.GET.get("url_name")
        print(app_name, url_name)
        request.session["language"] = request.GET.get("language")
        return redirect(reverse(f"{app_name}:{url_name}"))


class IndexView(View):
    template_name = "marketplace/index.html"

    def get(self, request, *args, **kwargs):
        evenements = (
            Evenement.objects.filter(est_actif=True).order_by("-date_debut").distinct()
        )

        slides = Slide.objects.filter(archive=True)

        evenements_avec_count = []
        for event in evenements:
            event.nb_interesses = event.interetevenement_set.filter(
                interesse=True
            ).count()
            evenements_avec_count.append(event)

        # Base queryset annonces approuvees, publiees
        approved_qs = (
            Announcement.objects.filter(
                status="approved",
                is_archived=False,
                publication_date__lte=timezone.now(),
            )
            .select_related("user", "category", "subcategory")
            .prefetch_related("tags")
        )

        # Categories ordonnees par nombre d'annonces (pour rails + mosaique)
        categories_with_count = (
            Category.objects.filter(is_archived=False)
            .annotate(
                annonces_count=Count(
                    "announcement",
                    filter=Q(
                        announcement__status="approved",
                        announcement__is_archived=False,
                    ),
                )
            )
            .prefetch_related("subcategories")
            .order_by("-annonces_count", "name")
        )

        # Rails par filiere : top 3 categories actives, 8 annonces chacune
        # On parcourt en Python car querysets imbriques inefficaces en SQL.
        top_categories = [c for c in categories_with_count if c.annonces_count > 0][:3]
        rails_by_category = []
        for cat in top_categories:
            rails_by_category.append(
                {
                    "category": cat,
                    "annonces": list(
                        approved_qs.filter(category=cat).order_by("-publication_date")[
                            :8
                        ]
                    ),
                }
            )

        # Spotlight = filiere la plus active (premiere des top_categories)
        spotlight = top_categories[0] if top_categories else None

        # Annonces populaires : par nombre de vues, sur les 60 derniers jours
        from datetime import timedelta

        sixty_days_ago = timezone.now() - timedelta(days=60)
        popular_annonces = list(
            approved_qs.filter(publication_date__gte=sixty_days_ago)
            .annotate(views_count=Count("views"))
            .order_by("-views_count", "-publication_date")[:6]
        )

        # Mosaique filieres : toutes les categories actives avec leur 1ere image
        # (issue de la 1ere annonce approuvee pour fournir un visuel).
        mosaic_categories = []
        for cat in categories_with_count[:9]:
            first_with_image = (
                approved_qs.filter(category=cat).exclude(image="").first()
            )
            mosaic_categories.append(
                {
                    "category": cat,
                    "cover_image": first_with_image.image if first_with_image else None,
                }
            )

        # Stats pour la barre KPI du hero (mix donnees reelles + positionnement)
        from accounts.models import Utilisateur

        hero_stats = {
            "producteurs": Utilisateur.objects.count(),
            "pays": 54,  # 54 pays africains (positionnement panafricain, pas
            # le count des annonces qui ne reflete pas la couverture cible)
            "filieres": SubCategory.objects.filter(is_archived=False).count(),
            "commission": "0%",
        }

        # Live ticker : 12 dernieres annonces approuvees pour la bande
        # defilante sous le hero. Selection legere (title + pays + filiere).
        live_ticker = list(
            approved_qs.order_by("-publication_date")[:12].values(
                "id", "title", "country", "category__name"
            )
        )

        # Compteurs pour le strip "Quick actions" sous le hero
        from datetime import timedelta

        seven_days_ago = timezone.now() - timedelta(days=7)
        new_annonces_7d = approved_qs.filter(
            publication_date__gte=seven_days_ago
        ).count()
        total_annonces_actives = approved_qs.count()

        quick_actions_counters = {
            "new_7d": new_annonces_7d,
            "total_active": total_annonces_actives,
            "sub_categories": SubCategory.objects.filter(is_archived=False).count(),
        }

        # Carte d'Afrique : nombre d'annonces actives par pays (dict code -> count)
        country_counts_qs = (
            approved_qs.exclude(country="")
            .values("country")
            .annotate(n=Count("id"))
        )
        country_counts = {c["country"]: c["n"] for c in country_counts_qs}
        active_countries_count = len(country_counts)

        # Producteur du mois : utilisateur avec le + d'annonces approuvees
        # actives. Annonce featured = sa derniere annonce avec image.
        from accounts.models import Utilisateur as _U

        producer_of_month = (
            _U.objects.annotate(
                n_active=Count(
                    "announcements",
                    filter=Q(
                        announcements__status="approved",
                        announcements__is_archived=False,
                    ),
                )
            )
            .filter(n_active__gt=0)
            .order_by("-n_active", "-date_joined")
            .first()
        )
        producer_featured_annonce = None
        if producer_of_month:
            producer_featured_annonce = (
                Announcement.objects.filter(
                    user=producer_of_month, status="approved", is_archived=False
                )
                .exclude(image="")
                .order_by("-publication_date")
                .first()
            )

        context = {
            "categories": categories_with_count,
            "annonces": list(approved_qs.order_by("-publication_date")[:8]),
            "rails_by_category": rails_by_category,
            "spotlight": spotlight,
            "popular_annonces": popular_annonces,
            "mosaic_categories": mosaic_categories,
            "hero_stats": hero_stats,
            "live_ticker": live_ticker,
            "quick_actions_counters": quick_actions_counters,
            "country_counts": country_counts,
            "active_countries_count": active_countries_count,
            "producer_of_month": producer_of_month,
            "producer_featured_annonce": producer_featured_annonce,
            "evenements": evenements_avec_count,
            "now": timezone.now(),
            "evenement": Evenement.objects.filter(slug="b2b-turin-2026").first(),
            "partenaires": Partenaire.objects.filter(archive=False),
            "sponsors": Sponsor.objects.filter(archive=False),
            "slides": slides,
        }

        return render(request, self.template_name, context)


# @method_decorator(cache_page(60 * 15), name="dispatch")
@method_decorator(never_cache, name="dispatch")
class CategoryView(View):
    template_name = "marketplace/category.html"
    items_per_page = 12

    def get(self, request, subcategory_id, *args, **kwargs):
        subcategory = get_object_or_404(
            SubCategory.objects.annotate(
                announcement_count=Count(
                    "announcements",
                    filter=Q(
                        announcements__status="approved",
                        announcements__is_archived=False,
                    ),
                )
            ),
            id=subcategory_id,
            is_archived=False,
        )

        main_category = subcategory.category_set.first()

        # Base queryset optimisé
        announcements = (
            Announcement.objects.filter(
                subcategory=subcategory,
                status="approved",
                is_archived=False,
                publication_date__lte=timezone.now(),
            )
            .select_related("user", "subcategory", "category")
            .prefetch_related("tags")
            .order_by("-publication_date")
        )

        # Filtrage
        search_term = request.GET.get("q")
        selected_types = request.GET.getlist("type")
        selected_country = request.GET.get("country")
        sort = request.GET.get("sort", "-publication_date")

        if search_term:
            announcements = announcements.filter(
                Q(title__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(tags__name__icontains=search_term)
            ).distinct()

        if selected_types:
            announcements = announcements.filter(type__in=selected_types)

        if selected_country:
            announcements = announcements.filter(country=selected_country)

        # Tri
        valid_sort_options = ["-publication_date", "title"]
        if sort in valid_sort_options:
            announcements = announcements.order_by(sort)

        # Pagination
        paginator = Paginator(announcements, self.items_per_page)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Sous-catégories apparentées
        if main_category:
            related_subcategories = (
                main_category.subcategories.exclude(id=subcategory_id)
                .annotate(
                    announcement_count=Count(
                        "announcements",
                        filter=Q(
                            announcements__status="approved",
                            announcements__is_archived=False,
                        ),
                    )
                )
                .order_by("-announcement_count", "name")
            )
        else:
            related_subcategories = SubCategory.objects.none()

        context = {
            "subcategory": subcategory,
            "category": main_category,
            "annonces": page_obj,
            "souscategories": related_subcategories,
            "search_term": search_term or "",
            "announcement_types": AnnouncementType.choices,
            "selected_types": selected_types,
            "selected_country": selected_country,
            "countries": countries,
            "AFRICAN_COUNTRY_CODES": settings.AFRICAN_COUNTRY_CODES,
        }
        return render(request, self.template_name, context)


class AnnoncesPays(View):
    template_name = "marketplace/annonces_pays.html"
    items_per_page = 10

    def get(self, request, afrique_id, *args, **kwargs):
        # Vérification stricte du code pays
        if not self.is_valid_country_code(afrique_id):
            # return render(request, "404.html", status=404)
            raise Http404("Pays non trouvé")

        country_name = countries.name(afrique_id)

        # Le reste du code inchangé...
        annonces_list = (
            Announcement.objects.filter(
                country=afrique_id,
                status="approved",
                is_archived=False,
                publication_date__lte=timezone.now(),
            )
            .select_related("category", "subcategory", "user")
            .prefetch_related("tags")
            .order_by("-publication_date")
        )

        paginator = Paginator(annonces_list, self.items_per_page)
        page_number = request.GET.get("page")
        annonces = paginator.get_page(page_number)

        context = {
            "annonces": annonces,
            "country_name": country_name,
            "country_code": afrique_id,
            "paginator": paginator,
            "page_obj": annonces,
        }

        return render(request, self.template_name, context)

    def is_valid_country_code(self, code):
        """Validation personnalisée des codes pays"""
        # Longueur valide (2 ou 3 caractères)
        if not (2 <= len(code) <= 3):
            return False

        # Vérifie que le code existe dans django-countries
        try:
            countries.name(code)
            return True
        except KeyError:
            return False


class CreateAnnouncementView(LoginRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = "marketplace/create_announcement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = Category.objects.filter(
            id=self.kwargs.get("category_id")
        ).first()
        context["subcategory"] = SubCategory.objects.filter(
            id=self.kwargs.get("subcategory_id")
        ).first()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["user"] = self.request.user

        if "category_id" in self.kwargs:
            initial["category"] = self.kwargs.get("category_id")
            if "subcategory_id" in self.kwargs:
                initial["subcategory"] = self.kwargs.get("subcategory_id")

        if self.request.user.pays and not initial.get("country"):
            initial["country"] = self.request.user.pays

        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Changement ici: utilisation du statut "pending_first" au lieu de "pending"
        form.instance.status = "pending_first"

        try:
            response = super().form_valid(form)
            # Appel de la méthode pour notifier les validateurs
            self.object._notify_validators("first")

            messages.success(
                self.request,
                _("Votre annonce a été soumise pour validation. Référence: {}").format(
                    self.object.reference
                ),
            )
            return response
        except Exception as e:
            messages.error(
                self.request, _("Une erreur est survenue : {}").format(str(e))
            )
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            "marketplace:announcement_detail", kwargs={"pk": self.object.pk}
        )

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        # Vérifier que la catégorie et sous-catégorie existent
        category_id = kwargs.get("category_id")
        subcategory_id = kwargs.get("subcategory_id")

        if not (
            Category.objects.filter(id=category_id).exists()
            and SubCategory.objects.filter(id=subcategory_id).exists()
        ):
            raise Http404

        return super().dispatch(request, *args, **kwargs)


# Dans votre vue ajax_load_subcategories
def ajax_load_subcategories(request):
    category_id = request.GET.get("category_id")

    if not category_id:
        return JsonResponse([], safe=False)

    try:
        category_id = int(category_id)
        subcategories = (
            SubCategory.objects.filter(category__id=category_id)
            .values("id", "name")
            .order_by("name")
        )

        data = list(subcategories)

    except (ValueError, TypeError):

        data = []

    return JsonResponse(data, safe=False)


class Create_AnnouncementView(LoginRequiredMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    # Reutilise le meme template moderne unifie (gere les 2 cas
    # avec/sans category dans URL grace au context).
    template_name = "marketplace/create_announcement.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        # kwargs["country"] = self.request.user.pays
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = "pending_first"

        response = super().form_valid(form)

        self.object._notify_validators("first")

        messages.success(
            self.request,
            _("Votre annonce a été soumise pour validation. Référence: {}").format(
                self.object.reference
            ),
        )
        return response

    def get_success_url(self):
        return reverse_lazy(
            "marketplace:announcement_detail",
            kwargs={"pk": self.object.pk},
        )


# class Create_AnnouncementView(LoginRequiredMixin, CreateView):
#     model = Announcement
#     form_class = AnnouncementForm
#     template_name = "marketplace/createannouncement.html"

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs["user"] = self.request.user
#         return kwargs

#     def get_initial(self):
#         initial = super().get_initial()
#         initial["user"] = self.request.user
#         if self.request.user.pays:
#             initial["country"] = self.request.user.pays
#         return initial

#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         form.instance.status = "pending_first"
#         try:
#             response = super().form_valid(form)
#             self.object._notify_validators("first")
#             messages.success(
#                 self.request,
#                 _("Votre annonce a été soumise pour validation. Référence: {}").format(
#                     self.object.reference
#                 ),
#             )
#             return response
#         except Exception as e:
#             messages.error(
#                 self.request, _("Une erreur est survenue : {}").format(str(e))
#             )
#             return self.form_invalid(form)

#     def form_invalid(self, form):
#         for field, errors in form.errors.items():
#             for error in errors:
#                 messages.error(self.request, f"{field}: {error}")
#         return super().form_invalid(form)

#     def get_success_url(self):
#         return reverse_lazy(
#             "marketplace:announcement_detail", kwargs={"pk": self.object.pk}
#         )


@method_decorator(login_required, name="dispatch")
class AnnouncementDetailView(DetailView):
    model = Announcement
    template_name = "marketplace/announcement_detail.html"
    context_object_name = "annonce"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Enregistrer la vue avec gestion des erreurs
        if not self.request.session.session_key:
            self.request.session.create()

        view_key = f"viewed_announcement_{self.object.id}"
        if not self.request.session.get(view_key, False):
            try:
                AnnouncementView.objects.create(
                    announcement=self.object,
                    user=(
                        self.request.user
                        if self.request.user.is_authenticated
                        else None
                    ),
                    ip_address=self.get_client_ip(),
                    session_key=self.request.session.session_key,
                )
                self.request.session[view_key] = True
            except IntegrityError:
                # L'entrée existe déjà, on marque quand même la session
                self.request.session[view_key] = True

        # Compter les vues
        context["view_count"] = AnnouncementView.objects.filter(
            announcement=self.object
        ).count()

        # Annonces similaires (meme categorie)
        context["similar_annonces"] = (
            Announcement.objects.filter(
                category=self.object.category,
                status="approved",
                is_archived=False,
            )
            .exclude(id=self.object.id)
            .select_related("user", "category")
            .order_by("-publication_date")[:6]
        )

        # Autres annonces du meme vendeur (NEW)
        context["seller_annonces"] = (
            Announcement.objects.filter(
                user=self.object.user, status="approved", is_archived=False
            )
            .exclude(id=self.object.id)
            .select_related("category")
            .order_by("-publication_date")[:4]
        )

        # Stats du vendeur
        seller_active_count = Announcement.objects.filter(
            user=self.object.user, status="approved", is_archived=False
        ).count()
        context["seller_active_count"] = seller_active_count

        context["can_edit"] = (
            self.request.user == self.object.user or self.request.user.is_superuser
        )

        return context

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip


class AllAnnouncementsListView(ListView):
    model = Announcement
    template_name = "marketplace/all_announcements.html"
    context_object_name = "annonces"
    paginate_by = 24

    SORT_CHOICES = {
        "recent": ("-publication_date", _("Plus récentes")),
        "old": ("publication_date", _("Plus anciennes")),
        "popular": ("-views_count", _("Plus consultées")),
    }

    def get_queryset(self):
        queryset = (
            Announcement.objects.filter(
                status="approved",
                is_archived=False,
                publication_date__lte=timezone.now(),
            )
            .select_related("user", "category", "subcategory")
            .prefetch_related("tags")
        )

        # Filtre par type d'annonce
        announcement_type = self.request.GET.get("type")
        if announcement_type:
            if announcement_type.lower() == "vente":
                queryset = queryset.filter(type=AnnouncementType.SALE)
            elif announcement_type.lower() == "achat":
                queryset = queryset.filter(type=AnnouncementType.PURCHASE)
            elif announcement_type.lower() == "autre":
                queryset = queryset.filter(type=AnnouncementType.OTHER)

        # Filtre par categorie
        cat_id = self.request.GET.get("cat")
        if cat_id and cat_id.isdigit():
            queryset = queryset.filter(category_id=int(cat_id))

        # Filtre par pays
        country = self.request.GET.get("country")
        if country:
            queryset = queryset.filter(country=country)

        # Filtre bio
        if self.request.GET.get("bio") == "1":
            queryset = queryset.filter(is_organic=True)

        # Recherche plein texte simple (titre + description + reference)
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(reference__icontains=q)
            )

        # Tri
        sort = self.request.GET.get("sort", "recent")
        if sort == "popular":
            queryset = queryset.annotate(views_count=Count("views")).order_by(
                "-views_count", "-publication_date"
            )
        elif sort == "old":
            queryset = queryset.order_by("publication_date")
        else:
            queryset = queryset.order_by("-publication_date")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = (
            Category.objects.prefetch_related("subcategories")
            .filter(is_archived=False)
            .annotate(
                annonces_count=Count(
                    "announcement",
                    filter=Q(
                        announcement__status="approved",
                        announcement__is_archived=False,
                    ),
                )
            )
            .order_by("-annonces_count", "name")
        )
        context["announcement_types"] = AnnouncementType.choices
        context["sort_choices"] = self.SORT_CHOICES
        current_sort = self.request.GET.get("sort", "recent")
        context["current_sort"] = current_sort
        context["current_sort_label"] = self.SORT_CHOICES.get(
            current_sort, self.SORT_CHOICES["recent"]
        )[1]

        # Preserved query string (sans page) pour la pagination
        get_params = self.request.GET.copy()
        if "page" in get_params:
            del get_params["page"]
        context["preserved_query"] = (
            "&" + get_params.urlencode() if get_params else ""
        )
        context["current_q"] = self.request.GET.get("q", "")
        context["current_cat"] = self.request.GET.get("cat", "")
        context["current_country"] = self.request.GET.get("country", "")
        context["current_bio"] = self.request.GET.get("bio") == "1"
        return context


class AnnouncementValidationView(LoginRequiredMixin, UpdateView):
    model = Announcement
    template_name = "marketplace/validate_announcement.html"

    def dispatch(self, request, *args, **kwargs):
        self.announcement = self.get_object()
        self.stage = (
            "first" if self.announcement.status == "pending_first" else "second"
        )
        # Controle d'acces : seul un validateur du bon niveau (et jamais
        # l'auteur de l'annonce) peut agir sur la validation/le rejet.
        if not self._can_validate(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _can_validate(self, user):
        if not user.is_authenticated:
            return False
        if self.announcement.user_id == user.id:
            return False
        group = f"announcement_{self.stage}_validators"
        return user.groups.filter(name=group).exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stage"] = self.stage
        return context


class ApproveAnnouncementView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        announcement = get_object_or_404(Announcement, pk=kwargs["pk"])

        # Vérification des permissions
        if not self._has_validation_permission(request.user, announcement):
            raise PermissionDenied

        # Logique de validation
        if announcement.status == "pending_first":
            announcement.approve_first(request.user)
        elif announcement.status == "pending_second":
            announcement.approve_second(request.user)

        messages.success(request, _("Validation effectuée avec succès."))
        return redirect("marketplace:announcement_detail", pk=announcement.pk)

    def _has_validation_permission(self, user, announcement):
        # Separation des taches : un validateur ne peut jamais valider sa
        # propre annonce, et le second validateur doit etre different du
        # premier (impossible pour une seule personne d'approuver seule).
        if announcement.user_id == user.id:
            return False
        if announcement.status == "pending_first":
            return user.groups.filter(name="announcement_first_validators").exists()
        elif announcement.status == "pending_second":
            if announcement.first_approver_id == user.id:
                return False
            return user.groups.filter(name="announcement_second_validators").exists()
        return False


class RejectAnnouncementView(AnnouncementValidationView):
    fields = ["rejection_reason"]

    def form_valid(self, form):
        self.announcement.reject(
            user=self.request.user, reason=form.cleaned_data["rejection_reason"]
        )
        messages.success(self.request, _("Annonce rejetée avec succès."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "marketplace:announcement_detail", kwargs={"pk": self.announcement.pk}
        )


class ValidatorDashboardView(LoginRequiredMixin, ListView):
    template_name = "marketplace/validator_dashboard.html"
    context_object_name = "announcements"

    def get_queryset(self):
        if self.request.user.groups.filter(
            name="announcement_first_validators"
        ).exists():
            return Announcement.objects.filter(status="pending_first")
        elif self.request.user.groups.filter(
            name="announcement_second_validators"
        ).exists():
            return Announcement.objects.filter(status="pending_second")
        return Announcement.objects.none()


class UserAnnouncementsView(LoginRequiredMixin, TemplateView):
    template_name = "marketplace/user_announcements.html"
    paginate_by = 10  # Nombre d'annonces par page pour chaque statut

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Announcement.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

        # Récupérer le numéro de page pour chaque statut depuis les paramètres GET
        draft_page = self.request.GET.get("draft_page", 1)
        pending_page = self.request.GET.get("pending_page", 1)
        approved_page = self.request.GET.get("approved_page", 1)
        rejected_page = self.request.GET.get("rejected_page", 1)

        # Création des paginateurs pour chaque statut
        context.update(
            {
                "draft_paginator": self._get_paginator(
                    queryset.filter(status="draft"), draft_page
                ),
                "pending_paginator": self._get_paginator(
                    queryset.filter(
                        Q(status="pending_first") | Q(status="pending_second")
                    ),
                    pending_page,
                ),
                "approved_paginator": self._get_paginator(
                    queryset.filter(status="approved"), approved_page
                ),
                "rejected_paginator": self._get_paginator(
                    queryset.filter(status="rejected"), rejected_page
                ),
            }
        )
        return context

    def _get_paginator(self, queryset, page_number):
        """Helper pour créer un paginator avec gestion des erreurs de page"""
        paginator = Paginator(queryset, self.paginate_by)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return page


class SubmitAnnouncementView(LoginRequiredMixin, View):
    def get(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk, user=request.user)

        if announcement.status != "draft":
            messages.error(
                request, _("Seules les annonces en brouillon peuvent être soumises")
            )
            return redirect("marketplace:user_announcements")

        try:
            announcement.status = "pending_first"
            announcement.save()
            announcement._notify_validators("first")
            messages.success(request, _("Annonce soumise avec succès pour validation"))
        except Exception as e:
            messages.error(
                request, _("Erreur lors de la soumission: {}").format(str(e))
            )

        return redirect("marketplace:user_announcements")


class ResubmitAnnouncementView(LoginRequiredMixin, View):
    def get(self, request, pk):
        announcement = get_object_or_404(Announcement, pk=pk, user=request.user)

        if announcement.status != "rejected":
            messages.error(
                request, _("Seules les annonces rejetées peuvent être resoumises")
            )
            return redirect("marketplace:user_announcements")

        try:
            announcement.status = "pending_first"
            announcement.rejection_reason = None
            announcement.save()
            announcement._notify_validators("first")
            messages.success(
                request, _("Annonce resoumise avec succès pour validation")
            )
        except Exception as e:
            messages.error(
                request, _("Erreur lors de la resoumission: {}").format(str(e))
            )

        return redirect("marketplace:user_announcements")


class SearchAnnouncementView(ListView):
    model = Announcement
    template_name = "marketplace/search_results.html"
    context_object_name = "announcements"
    paginate_by = 24

    def post(self, request, *args, **kwargs):
        # Compatibilite legacy : ancien form de recherche header (POST)
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_queryset(self):
        # Lit aussi bien GET (?q=, ?type=, ?country=) que POST (reference, subcategory)
        data = self.request.POST if self.request.method == "POST" else self.request.GET

        self.q = data.get("q", "").strip()
        self.reference = data.get("reference", "").strip()
        self.subcategory_id = data.get("subcategory", "").strip()
        self.type = data.get("type", "").strip()
        self.country = data.get("country", "").strip()

        queryset = (
            Announcement.objects.filter(
                status="approved",
                is_archived=False,
                publication_date__lte=timezone.now(),
            )
            .select_related("user", "category", "subcategory")
            .prefetch_related("tags")
        )

        filters = Q()
        if self.q:
            filters &= (
                Q(title__icontains=self.q)
                | Q(description__icontains=self.q)
                | Q(reference__icontains=self.q)
                | Q(tags__name__icontains=self.q)
            )
        if self.reference:
            filters &= Q(reference__icontains=self.reference)
        if self.subcategory_id:
            try:
                filters &= Q(subcategory__id=int(self.subcategory_id))
            except ValueError:
                pass
        if self.type in ("vente", "achat", "autre"):
            filters &= Q(type=self.type)
        if self.country:
            filters &= Q(country=self.country)

        if filters:
            queryset = queryset.filter(filters)

        return queryset.order_by("-publication_date").distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "q": self.q,
                "reference": self.reference,
                "subcategory": self.subcategory_id,
                "type": self.type,
                "country": self.country,
                "subcategories": SubCategory.objects.all(),
            }
        )
        return context
