# Guide de Contribution - IDA Marketplace

Bienvenue dans le projet **IDA Marketplace** ! Nous sommes une équipe de bénévoles travaillant ensemble pour développer une plateforme de vente en ligne avec Django. Ce document décrit comment contribuer efficacement au projet.

## 🚀 Objectif du Projet

IDA Marketplace vise à fournir une plateforme de vente en ligne où les utilisateurs peuvent publier et gérer des annonces de vente de produits.

## 🛠 Pré-requis

Avant de contribuer, assurez-vous d'avoir :

- Python 3.10+ installé
- Un environnement virtuel configuré (`python -m venv .env`)
- Les dépendances installées : `pip install -r requirements.txt`
- Une base de données configurée (`sqlite3` ou `PostgreSQL` selon les besoins)
- `pre-commit` installé et configuré

## 🔐 Configuration des variables d'environnement

Le projet utilise un fichier `.env` pour stocker les informations sensibles (comme les identifiants email, clés d'API, etc.).

### 📄 Étapes pour configurer le `.env` localement

1. **Créer un fichier `.env` à la racine du projet** (si ce n’est pas déjà fait) :
   ```bash
   touch .env
   ```

2. **Y coller les variables suivantes avec vos propres valeurs** :
   ```env
   EMAIL_HOST=your_email_host
   EMAIL_USE_TLS=True
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email_user
   EMAIL_HOST_PASSWORD=your_email_password
   DEFAULT_FROM_EMAIL=your_default_from_email
   EMAIL_FROM=your_email_from

   AWS_REGION=your_aws_region
   AWS_ACCESS_KEY_ID=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   ```

3. **(Optionnel mais recommandé)** : Ajouter le fichier `.env` dans `.gitignore` pour éviter de l’envoyer accidentellement :
   ```
   .env
   ```

4. **Installer la dépendance si nécessaire** :
   ```bash
   pip install python-dotenv
   ```

> Le chargement automatique des variables est déjà pris en charge dans `settings.py` :
```python
from dotenv import load_dotenv
load_dotenv()
```

## ⚙️ Configuration de `pre-commit`

Nous utilisons `pre-commit` pour garantir une qualité de code uniforme et éviter les erreurs courantes. Suivez ces étapes pour l'installer et l'utiliser :

1. **Installer `pre-commit` et les outils nécessaires**
   ```sh
   pip install pre-commit pytest flake8 isort mypy
   ```

2. **Ajouter les hooks** (déjà configurés dans `.pre-commit-config.yaml`)
   ```sh
   pre-commit install
   ```

3. **Exécuter manuellement `pre-commit` sur tous les fichiers** (optionnel, mais recommandé pour vérifier le code existant)
   ```sh
   pre-commit run --all-files
   ```

### Hooks configurés dans `pre-commit`

| Hook                   | Fonction                                             |
|------------------------|------------------------------------------------------|
| `black`                | Formate automatiquement le code selon PEP 8          |
| `isort`                | Organise les imports Python de manière cohérente     |
| `flake8`               | Analyse statiquement le code pour détecter des erreurs |
| `mypy`                 | Vérifie le typage statique du code                   |
| `pytest`               | Exécute les tests unitaires avant chaque commit      |
| `trailing-whitespace`  | Supprime les espaces inutiles en fin de ligne        |
| `end-of-file-fixer`    | Vérifie qu’un fichier se termine par une ligne vide  |
| `check-yaml`           | Vérifie la validité des fichiers YAML                |
| `check-json`           | Vérifie la validité des fichiers JSON                |
| `check-merge-conflict` | Détecte les conflits Git non résolus                |
| `detect-private-key`   | Empêche l’ajout de clés privées dans le dépôt        |

### Pourquoi utiliser `pre-commit` ?

- Assure un code propre avant chaque commit
- Applique automatiquement des corrections simples (espaces inutiles, formatage, etc.)
- Empêche l’ajout de fichiers mal formatés dans le dépôt
- Exécute les tests unitaires pour éviter des régressions

## 📌 Workflow Git

Nous utilisons **Git** et **GitLab** pour la gestion du code. Voici les étapes à suivre pour contribuer :

1. **Cloner le dépôt**
   ```sh
   git clone https://gitlab.com/nom-utilisateur/IDAMarketplace.git
   cd IDAMarketplace
   ```

2. **Créer une branche** (basée sur `develop`)
   ```sh
   git checkout develop
   git pull origin develop
   git checkout -b feature/nom-fonctionnalite
   ```

3. **Faire des modifications** et les tester

4. **Committer les changements** (après exécution de `pre-commit`)
   ```sh
   git add .
   git commit -m "Ajout de la fonctionnalité X"
   ```

5. **Pousser la branche et créer une Merge Request (MR)**
   ```sh
   git push origin feature/nom-fonctionnalite
   ```
   - Ouvrir une MR sur GitLab vers la branche `develop`
   - Un relecteur vérifiera le code avant fusion

## 🎨 Conventions de Code

Nous suivons ces standards :

- **PEP 8** pour le style Python
- **Black** pour le formatage automatique du code
- **Respect des bonnes pratiques Django**
- **Tests obligatoires avec pytest avant tout merge**

## 🐞 Signaler un Bug / Proposer une Amélioration

Les bugs et suggestions doivent être signalés via **GitLab Issues** avec une description claire et, si possible, des captures d'écran ou logs.

## 📝 Contact

Si vous avez des questions, contactez l'un des mainteneurs du projet ou ouvrez une discussion sur GitLab.

Merci pour votre contribution et votre engagement ! 🚀
