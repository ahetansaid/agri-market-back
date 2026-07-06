# IDA Marketplace

Bienvenue sur le dépôt GitHub de **IDA Marketplace**, une plateforme numérique innovante conçue pour dynamiser le secteur agricole en facilitant la mise en relation entre agriculteurs à fort potentiel et chercheurs d'opportunités.

![Logo IDA](https://ida.worldbank.org/sites/ida.worldbank.org/files/styles/ida_banner_1920x500/public/images/2022-09/about-ida_hero.jpg) <!-- lien fictif à remplacer -->

---
Voici une version simplifiée pour votre README.md :


## 🛠 Configuration de la base de données

### Option 1 : SQLite (par défaut)
Aucune configuration nécessaire - fonctionne immédiatement

### Option 2 : PostgreSQL (recommandé)

1. Installer PostgreSQL :
```bash
sudo apt install postgresql
```

2. Créer la base et l'utilisateur :
```bash
sudo -u postgres psql -c "CREATE DATABASE marketplace_db;"
sudo -u postgres psql -c "CREATE USER marketplace_user WITH PASSWORD 'monmotdepasse';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE marketplace_db TO marketplace_user;"
```

3. Ajouter au fichier `.env` :
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=marketplace_db
DB_USER=marketplace_user
DB_PASSWORD=monmotdepasse
DB_HOST=localhost
DB_PORT=5432
```

4. Installer le connecteur :
```bash
pip install psycopg2-binary
```

5. Lancer les migrations :
```bash
python manage.py migrate
```
---

### 🔐 Conseils importants
- Choisissez un mot de passe fort
- Ne partagez jamais votre fichier `.env`
- Pour la production, activez SSL


## 🚀 Démarrage Rapide

### Prérequis
- Python 3.10+
- PostgreSQL (recommandé) ou SQLite
- Node.js 16+ (pour les assets frontend)

### Installation
```bash
git clone https://github.com/votre-repo/ida-marketplace.git
cd ida-marketplace
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate pour Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata 01_subcategories 02_categories
python manage.py createsuperuser
python manage.py runserver
```

Accédez à l'interface d'administration :
`http://localhost:8000/admin`

### 🔐 Configuration des groupes de validation

Le système de validation à deux niveaux nécessite la création de groupes spécifiques dans l'interface d'administration Django :

1. **Groupes requis** :
   - `announcement_first_validators` (Premier niveau de validation)
   - `announcement_second_validators` (Second niveau de validation)

2. **Pour créer les groupes** :
   - Accédez à l'interface admin (`/admin`)
   - Allez dans "Auth" > "Groups"
   - Ajoutez les deux groupes mentionnés ci-dessus

3. **Attribution des permissions** :
   - Assignez les utilisateurs validateurs aux groupes appropriés
   - Vous pouvez restreindre par catégorie si nécessaire

#### ⚙️ Workflow de validation

Le processus de publication d'une annonce suit ces étapes :

1. **Soumission** :
   - L'annonce est créée avec le statut `draft`
   - Lors de la soumission, passe en `pending_first`

2. **Première validation** :
   - Seuls les membres du groupe `announcement_first_validators` peuvent valider
   - Après approbation, statut passe à `pending_second`

3. **Seconde validation** :
   - Seuls les membres du groupe `announcement_second_validators` peuvent valider
   - Après approbation, statut passe à `approved` et l'annonce est publiée

4. **Rejet** :
   - À tout moment, un validateur peut rejeter avec une raison
   - L'annonce passe au statut `rejected`
   - Le créateur est notifié par email
---

## 🌎 Vision du projet

IDA Marketplace est inspirée par la mission de l'**Association Internationale de Développement (IDA)**, qui soutient la croissance inclusive dans les pays en développement. Ce projet vise à catalyser les investissements dans l'agriculture à travers une marketplace moderne, inclusive et transparente.

**Objectifs principaux :**
- 🚶 Créer un lien direct entre producteurs agricoles et investisseurs.
- 📈 Stimuler l'économie locale par la valorisation des produits agricoles.
- 🚀 Soutenir l'innovation, la collaboration et la professionnalisation du secteur agricole.

---

## 🛠 Fonctionnalités Clés

### 📊 Gestion des Produits
- 7 catégories principales et 41 sous-catégories préconfigurées
- Système complet d'annonces avec images redimensionnées automatiquement
- Filtrage par pays africains et devises locales

### 👤 Expérience Utilisateur
- Interface adaptée aux marchés africains
- Gestion multilingue (français/anglais)
- Profils dédiés pour agriculteurs et acheteurs

### ⚙️ Pour les Développeurs
```bash
# Charger les données initiales
python manage.py loaddata 01_subcategories 02_categories

# Exporter les données actuelles
python manage.py dumpdata marketplace.Category marketplace.SubCategory --indent 2 > marketplace/fixtures/updated_data.json
```

---

## 📆 Roadmap & Stories utilisateurs

- [x] Système de catégories/sous-catégories
- [ ] Gestion des annonces produits
- [ ] Système de messagerie interne
- [ ] Tableau de bord analytique

---

## 🗃 Structure des Données

| Fichier                | Description                              |
|------------------------|------------------------------------------|
| `01_subcategories.json`| 41 sous-catégories agricoles complètes   |
| `02_categories.json`   | 7 catégories principales avec relations |

Exemple de vérification :
```python
from marketplace.models import Category
for cat in Category.objects.all():
    print(f"{cat.name} -> {[s.name for s in cat.subcategories.all()]}")
```

---

## 🚀 Fonctionnalités Clés

Voici les fonctionnalités principales, issues d'une analyse critique des besoins utilisateurs :

### 👤 Gestion de compte
- Enregistrement en tant que **client**, **vendeur** ou **investisseur**.
- Possibilité de créer un **profil d'entreprise** (vendeur).
- Statuts VIP/VVIP avec avantages (visibilité accrue, accès prioritaire).

### 📊 Marketplace & Annonces
- Publication d'annonces (produits, services, opportunités).
- Classement par **catégories** et **filtres avancés**.
- Possibilité de **mettre en avant** des annonces (services premium).
- Système de **favoris** et de **showroom dédié**.

### 📨 Messagerie & Notifications
- ✉️ Messagerie interne (chat ou email privé).
- Alertes personnalisées basées sur des mots-clés.
- Notifications en temps réel.

### 🌐 Accessibilité
- 📱 Version responsive pour mobile et tablette.
- 🇳🇱🇸🇲 Multilingue : français et anglais.

### ✨ Crédibilité & Fiabilité
- 📊 Système d'évaluation et de réputation (notes & avis).
- 🤝 Témoignages vérifiés.
- ⚠️ Modération et vérification des annonces.

### 🌟 Services Premium
- Mise en avant d'annonces.
- Accès à des analyses de performances.
- Positionnement préférentiel dans les recherches.

### 🚫 Sécurité & Confiance
- Contrôle et vérification des vendeurs.
- Modération automatique et manuelle.
- Outils anti-fraude pour protéger la communauté.

### 🛌 Support & Assistance
- 😊 FAQ, chat d'aide et support technique 24/7.

---

## 🎓 Utilisateurs Cibles

- **Agriculteurs/Vendeurs** : Souhaitent exposer leurs produits et attirer de nouveaux clients.
- **Clients/Investisseurs** : Cherchent des opportunités fiables dans le secteur agricole.
- **Administrateurs** : Gèrent les activités, modèrent les annonces et accompagnent les utilisateurs.

---

## 📆 Roadmap & Stories utilisateurs (extrait)

- [x] Création et gestion de compte
- [x] Publication et modification des annonces
- [ ] Système de messagerie interne
- [ ] Paiement et abonnement pour services premium
- [ ] Intégration showroom matériels
- [ ] Interface multilingue
- [ ] Notifications push
- [ ] Panel administrateur

---

## 🌐 API Documentation

L'application expose une API RESTful complète pour interagir avec les fonctionnalités des événements.

### 📌 Points d'accès

#### Événements
- `GET /api/evenements/` - Liste tous les événements actifs
- `GET /api/evenements/{slug}/` - Détails d'un événement spécifique
- `POST /api/evenements/{slug}/inscription/` - S'inscrire à un événement
- `DELETE /api/evenements/{slug}/desinscription/` - Se désinscrire d'un événement

### 🔍 Documentation interactive

Nous fournissons trois façons d'accéder à la documentation :

1. **Swagger UI** (recommandé pour le développement) :
   [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
   *Interface interactive permettant de tester les endpoints directement*

2. **ReDoc** (documentation plus lisible) :
   [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
   *Version plus propre pour partager avec les consommateurs de l'API*

3. **Schéma OpenAPI brut** :
   [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
   *Fichier JSON utilisable pour générer des clients API*

### 🔑 Authentification

| Type | Utilisation |
|------|------------|
| Aucune | Pour la lecture et les inscriptions |
| Token/Session | Pour les opérations d'administration |

### 📝 Exemple d'inscription

```bash
curl -X 'POST' \
  'http://localhost:8000/api/evenements/turing/inscription/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "nom_complet": "Jean Dupont",
    "email": "jean@example.com",
    "interesse": true,
    "accepte_newsletter": true
  }'
```

## 📝 Création de formulaires dynamiques

### Fonctionnement des formulaires d'événements

1. **Dans l'admin Django** :
   - Créez un **Questionnaire** dans la section dédiée
   - Ajoutez des **Sections** pour organiser les questions
   - Insérez des **Questions** avec leurs types (texte, choix multiple, fichier, etc.)

2. **Types de questions disponibles** :
   ```plaintext
   TC - Texte court (une ligne)
   TL - Texte long (paragraphe)
   CU - Choix unique (boutons radio)
   CM - Choix multiples (cases à cocher)
   LD - Liste déroulante
   DT - Date
   FL - Fichier à uploader
   BL - Oui/Non (case à cocher)
   ```

3. **Lier à un événement** :
   - Lors de la création/modification d'un événement
   - Sélectionnez le questionnaire dans le champ dédié
   - Le formulaire sera généré automatiquement sur la page d'inscription

4. **Gestion des réponses** :
   - Toutes les réponses sont enregistrées
   - Accessibles via l'interface admin
   - Exportables en CSV

**Astuce** : Utilisez le champ "Ordre" pour contrôler l'affichage des questions.


## ✍️ Contribution

Les contributions sont les bienvenues ! Pour en savoir plus sur la manière de contribuer, consultez le fichier [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 👏 Remerciements

Un grand merci à tous les contributeurs et partenaires qui accompagnent la vision d'IDA Marketplace.
Ensemble, nous créons un avenir agricole plus connecté, plus prospère et plus durable.

---

> Inspiré par la mission de l'IDA : [https://ida.worldbank.org](https://ida.worldbank.org)
