from django.db import migrations

INTRO = (
    "Agri Market Africa est une plateforme née d'une vision : promouvoir et "
    "valoriser l'agriculture africaine de qualité supérieure. Dédiée à la "
    "valorisation, la commercialisation et la promotion des produits agricoles "
    "africains, elle a été conçue pour offrir aux producteurs, coopératives, "
    "transformateurs et distributeurs un espace moderne, sécurisé et "
    "transparent, leur permettant d'accéder facilement aux marchés locaux, "
    "régionaux et internationaux. En intégrant l'innovation numérique au "
    "service de l'agriculture, nous facilitons les échanges, renforçons la "
    "visibilité des produits africains et favorisons des partenariats durables. "
    "Plus qu'un simple marché en ligne, notre initiative constitue un véritable "
    "écosystème de croissance, où l'offre rencontre la demande dans un cadre "
    "équitable et responsable. Notre ambition est de contribuer activement à "
    "l'autonomie économique des acteurs agricoles africains, à la sécurité "
    "alimentaire et à la reconnaissance des produits du continent comme des "
    "références de qualité et de durabilité à l'échelle mondiale."
)

VISION = (
    "Devenir la principale plateforme panafricaine de référence pour la "
    "valorisation, la commercialisation et la transformation des produits "
    "agricoles africains, en connectant producteurs, transformateurs, "
    "distributeurs et consommateurs sur un marché moderne, transparent et "
    "inclusif. Construire un écosystème numérique agricole qui renforce "
    "l'autonomie économique des producteurs africains et promeut l'Afrique "
    "comme un acteur majeur de la sécurité alimentaire mondiale."
)

PERSPECTIVES = (
    "Élargir la présence de la marketplace à l'ensemble des pays africains et "
    "établir des passerelles commerciales solides avec les marchés "
    "internationaux. Développer notre certification NourDign, afin de garantir "
    "la qualité et l'origine des produits agricoles africains. Intégrer des "
    "solutions de financement innovantes pour accompagner les producteurs et "
    "coopératives dans leur croissance. Créer un hub panafricain de données "
    "agricoles, favorisant la prise de décision éclairée et la mise en place de "
    "politiques agricoles efficaces. Contribuer à faire de l'Afrique non "
    "seulement le grenier du monde, mais également un pôle d'innovation "
    "agroalimentaire reconnu et compétitif."
)

MISSION = (
    "Offrir une solution innovante de mise en marché et de distribution pour "
    "les produits agricoles africains, tout en favorisant la traçabilité, la "
    "qualité et la durabilité. Faciliter l'accès des producteurs africains aux "
    "marchés locaux, régionaux et internationaux grâce à des outils numériques "
    "performants et à des partenariats stratégiques. Accompagner la transition "
    "agricole vers des modèles plus compétitifs, équitables et respectueux de "
    "l'environnement."
)

VALUES = [
    (
        "Award",
        "Excellence",
        "Garantir des standards élevés de qualité et de service pour répondre "
        "aux attentes des marchés locaux et internationaux.",
    ),
    (
        "Leaf",
        "Durabilité",
        "Mettre en avant des pratiques agricoles responsables qui protègent les "
        "ressources naturelles et les générations futures.",
    ),
    (
        "Users",
        "Solidarité",
        "Renforcer la coopération entre producteurs, coopératives, PME et "
        "partenaires institutionnels afin de bâtir un marché inclusif.",
    ),
    (
        "Lightbulb",
        "Innovation",
        "Promouvoir l'usage des technologies numériques pour moderniser et "
        "optimiser la chaîne de valeur agricole.",
    ),
    (
        "ShieldCheck",
        "Intégrité",
        "Assurer transparence et équité dans toutes les transactions et "
        "relations commerciales.",
    ),
]


def seed(apps, schema_editor):
    AboutPage = apps.get_model("blog", "AboutPage")
    AboutValue = apps.get_model("blog", "AboutValue")
    if AboutPage.objects.exists():
        return
    page = AboutPage.objects.create(
        title="À propos de Agri Market Africa",
        title_fr="À propos de Agri Market Africa",
        intro=INTRO,
        intro_fr=INTRO,
        vision_title="Notre vision",
        vision_title_fr="Notre vision",
        vision=VISION,
        vision_fr=VISION,
        perspectives_title="Nos perspectives d'avenir",
        perspectives_title_fr="Nos perspectives d'avenir",
        perspectives=PERSPECTIVES,
        perspectives_fr=PERSPECTIVES,
        values_title="Nos valeurs",
        values_title_fr="Nos valeurs",
        mission_title="Notre mission",
        mission_title_fr="Notre mission",
        mission=MISSION,
        mission_fr=MISSION,
        is_active=True,
    )
    for order, (icon, title, desc) in enumerate(VALUES):
        AboutValue.objects.create(
            page=page,
            icon=icon,
            title=title,
            title_fr=title,
            description=desc,
            description_fr=desc,
            order=order,
        )


def unseed(apps, schema_editor):
    AboutPage = apps.get_model("blog", "AboutPage")
    AboutPage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0004_aboutpage_aboutvalue"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
