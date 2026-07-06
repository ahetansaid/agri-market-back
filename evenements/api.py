from django.utils.timezone import now
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import (
    Evenement,
    InteretEvenement,
    Question,
    Questionnaire,
    ReponseQuestion,
    SectionQuestionnaire,
)


class ReponseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReponseQuestion
        fields = ["id", "question", "valeur", "fichier"]
        extra_kwargs = {
            "question": {"read_only": True},
            "fichier": {"read_only": True},
        }


class InteretEvenementSerializer(serializers.ModelSerializer):
    reponses = ReponseQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = InteretEvenement
        fields = [
            "id",
            "utilisateur",
            "nom_complet",
            "email",
            "telephone",
            "date_creation",
            "reponses",
        ]
        extra_kwargs = {
            "utilisateur": {"read_only": True},
            "email": {"required": True},
            "nom_complet": {"required": True},
        }


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "libelle",
            "type_question",
            "options",
            "obligatoire",
            "aide_texte",
        ]


class SectionQuestionnaireSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = SectionQuestionnaire
        fields = ["id", "nom", "description", "ordre", "questions"]


class QuestionnaireSerializer(serializers.ModelSerializer):
    sections = SectionQuestionnaireSerializer(many=True, read_only=True)

    class Meta:
        model = Questionnaire
        fields = ["id", "nom", "actif", "date_creation", "sections"]


class EvenementSerializer(serializers.ModelSerializer):
    nb_interesses = serializers.SerializerMethodField()
    est_inscrit = serializers.SerializerMethodField()
    prochain_evenement = serializers.SerializerMethodField()
    questionnaire = QuestionnaireSerializer(read_only=True)

    class Meta:
        model = Evenement
        fields = [
            "id",
            "titre",
            "slug",
            "description_fr",
            "description_en",
            "description_it",
            "image_fr",
            "image_en",
            "image_it",
            "date_debut",
            "date_fin",
            "est_actif",
            "nb_interesses",
            "est_inscrit",
            "prochain_evenement",
            "questionnaire",
        ]
        read_only_fields = ["slug", "est_actif", "nb_interesses", "est_inscrit"]
        extra_kwargs = {
            "titre": {
                "help_text": "Titre de l'événement (50 caractères max)",
                "required": True,
            },
            "description_fr": {
                "help_text": "Description détaillée de l'événement (HTML autorisé)"
            },
            "description_en": {
                "help_text": "Description détaillée de l'événement (HTML autorisé)"
            },
            "description_it": {
                "help_text": "Description détaillée de l'événement (HTML autorisé)"
            },
            "image_fr": {
                "help_text": "Image de couverture de l'événement (format JPEG/PNG)"
            },
            "image_en": {
                "help_text": "Image de couverture de l'événement (format JPEG/PNG)"
            },
            "image_it": {
                "help_text": "Image de couverture de l'événement (format JPEG/PNG)"
            },
            "date_debut": {
                "help_text": "Date et heure de début (format ISO 8601: YYYY-MM-DDTHH:MM:SSZ)"
            },
            "date_fin": {
                "help_text": "Date et heure de fin (doit être après la date de début)"
            },
            "est_actif": {
                "help_text": "Uniquement les événements actifs sont visibles publiquement"
            },
        }

    def get_nb_interesses(self, obj):
        return obj.count_interesses()

    def get_est_inscrit(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.interetevenement_set.filter(
                utilisateur=request.user, interesse=True
            ).exists()
        return False

    def get_prochain_evenement(self, obj):
        return obj.date_debut > now()


@extend_schema_view(
    list=extend_schema(
        summary="Lister tous les événements",
        description="Retourne une liste paginée de tous les événements actifs.",
        responses={200: EvenementSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Exemple de réponse",
                value=[
                    {
                        "id": 1,
                        "titre": "Conférence Tech",
                        "slug": "conference-tech",
                        "description_fr": "Conférence sur les dernières technologies...",
                        "description_en": "Conférence sur les dernières technologies...",
                        "description_it": "Conférence sur les dernières technologies...",
                        "date_debut": "2023-06-15T09:00:00Z",
                        "date_fin": "2023-06-15T18:00:00Z",
                        "nb_interesses": 42,
                        "est_inscrit": False,
                        "prochain_evenement": True,
                    }
                ],
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Récupérer un événement",
        description="Retourne les détails complets d'un événement spécifique.",
        parameters=[
            OpenApiParameter(
                name="slug",
                type=str,
                location=OpenApiParameter.PATH,
                description="Slug unique de l'événement",
            )
        ],
    ),
    create=extend_schema(
        summary="Créer un événement",
        description="Endpoint réservé aux administrateurs pour créer un nouvel événement.",
        request=EvenementSerializer,
        responses={201: EvenementSerializer},
    ),
    update=extend_schema(
        summary="Mettre à jour un événement",
        description="Endpoint réservé aux administrateurs pour mettre à jour un événement.",
        request=EvenementSerializer,
        responses={200: EvenementSerializer},
    ),
    partial_update=extend_schema(
        summary="Mettre à jour partiellement un événement",
        description="Endpoint réservé aux administrateurs pour mettre à jour partiellement un événement.",
        request=EvenementSerializer,
        responses={200: EvenementSerializer},
    ),
    destroy=extend_schema(
        summary="Supprimer un événement",
        description="Endpoint réservé aux administrateurs pour supprimer un événement.",
        responses={204: None},
    ),
)
class EvenementViewSet(viewsets.ModelViewSet):
    """
    API endpoint permettant de gérer les événements.

    Les utilisateurs authentifiés peuvent :
    - Voir la liste des événements
    - Voir les détails d'un événement
    - Gérer leurs inscriptions

    Les administrateurs peuvent en plus :
    - Créer/modifier/supprimer des événements
    """

    queryset = Evenement.objects.filter(est_actif=True).order_by("-date_debut")
    serializer_class = EvenementSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    @extend_schema(
        methods=["GET"],
        summary="Vérifier son inscription",
        description="Vérifie si l'utilisateur courant ou l'email fourni est inscrit à l'événement.",
        parameters=[
            OpenApiParameter(
                name="email",
                type=OpenApiTypes.EMAIL,
                location=OpenApiParameter.QUERY,
                description="Email à vérifier (requis si utilisateur non authentifié)",
            )
        ],
        responses={
            200: InteretEvenementSerializer,
            404: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Utilisateur authentifié",
                value={
                    "id": 1,
                    "nom_complet": "Jean Dupont",
                    "email": "jean@example.com",
                    "interesse": True,
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Non inscrit",
                value={"detail": "Non inscrit"},
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    @extend_schema(
        methods=["POST"],
        summary="S'inscrire à un événement",
        description="Permet à un utilisateur de s'inscrire à un événement.",
        request=InteretEvenementSerializer,
        responses={
            201: InteretEvenementSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Requête type",
                value={
                    "nom_complet": "Jean Dupont",
                    "email": "jean@example.com",
                    "interesse": True,
                    "accepte_newsletter": True,
                },
                request_only=True,
            )
        ],
    )
    @extend_schema(
        methods=["PUT", "PATCH"],
        summary="Modifier son inscription",
        description="Permet de mettre à jour les informations d'inscription.",
        request=InteretEvenementSerializer,
        responses={
            200: InteretEvenementSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(
        detail=True, methods=["get", "post", "put", "patch"], url_path="inscription"
    )
    def gestion_inscription(self, request, slug=None):
        evenement = self.get_object()

        if request.method == "GET":
            if request.user.is_authenticated:
                inscription = InteretEvenement.objects.filter(
                    evenement=evenement, utilisateur=request.user
                ).first()
            else:
                email = request.query_params.get("email")
                if email:
                    inscription = InteretEvenement.objects.filter(
                        evenement=evenement, email=email
                    ).first()
                else:
                    return Response(
                        {
                            "detail": "Email requis pour les utilisateurs non authentifiés"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if inscription:
                serializer = InteretEvenementSerializer(inscription)
                return Response(serializer.data)
            return Response({"detail": "Non inscrit"}, status=status.HTTP_404_NOT_FOUND)

        elif request.method in ["POST", "PUT", "PATCH"]:
            data = request.data.copy()
            if request.user.is_authenticated:
                data["utilisateur"] = request.user.id
                email = request.user.email
            else:
                email = data.get("email")

            if email:
                inscription = InteretEvenement.objects.filter(
                    email=email, evenement=evenement
                ).first()

                if inscription and request.method == "POST":
                    return Response(
                        {"detail": "Vous êtes déjà inscrit à cet événement"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if request.method in ["PUT", "PATCH"] and not inscription:
                    return Response(
                        {"detail": "Inscription non trouvée"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {"detail": "Email requis"}, status=status.HTTP_400_BAD_REQUEST
                )

            serializer = InteretEvenementSerializer(
                instance=inscription if request.method in ["PUT", "PATCH"] else None,
                data=data,
                partial=request.method == "PATCH",
            )

            if serializer.is_valid():
                serializer.save(evenement=evenement)
                return Response(
                    serializer.data,
                    status=(
                        status.HTTP_201_CREATED
                        if request.method == "POST"
                        else status.HTTP_200_OK
                    ),
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        methods=["DELETE"],
        summary="Se désinscrire",
        description="Permet de se désinscrire d'un événement.",
        responses={
            204: None,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Requête authentifiée",
                value=None,
                request_only=True,
                status_codes=["204"],
            ),
            OpenApiExample(
                "Requête anonyme",
                value={"email": "jean@example.com"},
                request_only=True,
                status_codes=["204"],
            ),
        ],
    )
    @action(detail=True, methods=["delete"], url_path="desinscription")
    def desinscription(self, request, slug=None):
        evenement = self.get_object()
        email = request.data.get("email") or (
            request.user.email if request.user.is_authenticated else None
        )

        if not email:
            return Response(
                {"detail": "Email requis pour les utilisateurs non authentifiés"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inscription = InteretEvenement.objects.filter(
            evenement=evenement, email=email
        ).first()

        if inscription:
            if (
                request.user.is_authenticated
                and inscription.utilisateur != request.user
            ):
                return Response(
                    {
                        "detail": "Vous n'avez pas la permission de supprimer cette inscription"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            inscription.delete()
            return Response(
                {"detail": "Désinscription effectuée"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"detail": "Inscription non trouvée"}, status=status.HTTP_404_NOT_FOUND
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_permissions(self):
        # Inscription / desinscription doivent etre authentifiees : sinon
        # n'importe qui peut spammer ou supprimer l'inscription d'autrui
        # par enumeration d'emails.
        if self.action in ["gestion_inscription", "desinscription"]:
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly()]
