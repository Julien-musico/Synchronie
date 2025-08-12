# 🎵 Synchronie - Musicothérapie assistée par IA

Synchronie révolutionne la pratique de la musicothérapie en automatisant la documentation des séances grâce à l'intelligence artificielle, tout en offrant des outils de suivi thérapeutique basés sur les standards internationaux.

## 🎯 Fonctionnalités principales

- **Transcription automatique** : Conversion audio → texte avec OpenAI Whisper
- **Analyse IA intelligente** : Synthèses thérapeutiques générées par Mistral AI
- **Grilles d'évaluation** : Standards internationaux (AMTA, IMCAP-ND) et personnalisées
- **Rapports automatisés** : Génération de rapports périodiques professionnels
- **Gestion de patients** : Dossiers complets et sécurisés
- **Conformité RGPD** : Sécurité et confidentialité des données

## 🛠️ Installation et configuration

### Prérequis

- Python 3.11+
- PostgreSQL 14+
- Redis (pour les tâches asynchrones)
- Git

### Installation

1. **Cloner le repository**
```bash
git clone https://github.com/votre-username/synchronie.git
cd synchronie
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de l'environnement**
```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos configurations :
```env
SECRET_KEY=votre-clé-secrète-très-sécurisée
DATABASE_URL=postgresql://username:password@localhost/synchronie_dev
OPENAI_API_KEY=votre-clé-openai
MISTRAL_API_KEY=votre-clé-mistral
```

5. **Configuration de la base de données**
```bash
# Créer la base de données PostgreSQL
createdb synchronie_dev

# Initialiser les tables
flask db upgrade
```

6. **Initialiser les données**
```bash
# Créer un utilisateur admin
flask create-admin

# Ajouter les grilles d'évaluation par défaut
flask seed-grilles
```

## 🚀 Démarrage

### Développement
```bash
flask run
```

L'application sera accessible sur `http://localhost:5000`

### Production (avec Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🏗️ Structure du projet

```
synchronie/
├── app/
│   ├── __init__.py              # Factory de l'application Flask
│   ├── models/                  # Modèles de données
│   │   ├── user.py             # Modèle utilisateur
│   │   ├── patient.py          # Modèle patient
│   │   ├── session.py          # Modèle séance
│   │   ├── grille.py           # Modèles grilles d'évaluation
│   │   └── rapport.py          # Modèle rapport
│   ├── routes/                  # Routes et contrôleurs
│   │   ├── main.py             # Routes principales
│   │   ├── auth.py             # Authentification
│   │   ├── patients.py         # Gestion patients
│   │   ├── sessions.py         # Gestion séances
│   │   ├── grilles.py          # Grilles d'évaluation
│   │   └── rapports.py         # Rapports
│   ├── services/                # Services métier
│   │   ├── audio_service.py    # Transcription audio
│   │   └── ai_service.py       # Analyse IA
│   ├── templates/               # Templates HTML
│   ├── static/                  # Fichiers statiques (CSS, JS)
│   └── utils/                   # Utilitaires
├── migrations/                  # Migrations de base de données
├── tests/                       # Tests unitaires
├── uploads/                     # Fichiers uploadés
├── config.py                    # Configuration
├── app.py                       # Point d'entrée
└── requirements.txt             # Dépendances Python
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=app

# Tests d'un module spécifique
pytest tests/test_models.py
```

## 📖 Utilisation

### 1. Connexion
- Utilisez les identifiants admin créés lors de l'installation
- Ou créez un nouvel utilisateur thérapeute

### 2. Gestion des patients
- Créez des dossiers patients complets
- Définissez les objectifs thérapeutiques
- Assignez des grilles d'évaluation

### 3. Séances de musicothérapie
- Planifiez vos séances
- Uploadez vos enregistrements audio
- La transcription et l'analyse se font automatiquement

### 4. Évaluation et suivi
- Cotez vos séances avec les grilles
- Visualisez l'évolution des patients
- Générez des rapports périodiques

## 🔧 Configuration avancée

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `SECRET_KEY` | Clé secrète Flask | - |
| `DATABASE_URL` | URL de la base PostgreSQL | - |
| `OPENAI_API_KEY` | Clé API OpenAI pour Whisper | - |
| `MISTRAL_API_KEY` | Clé API Mistral AI | - |
| `CELERY_BROKER_URL` | URL Redis pour Celery | `redis://localhost:6379` |
| `MAIL_SERVER` | Serveur SMTP | - |
| `MAIL_USERNAME` | Utilisateur email | - |
| `MAIL_PASSWORD` | Mot de passe email | - |

### Déploiement sur Render.com

1. Connectez votre repository GitHub
2. Configurez les variables d'environnement
3. Le déploiement se fait automatiquement

## 🏥 Standards de musicothérapie intégrés

- **AMTA** : Association Américaine de Musicothérapie
- **IMCAP-ND** : Grille spécialisée troubles autistiques
- **MRS** : Musicothérapie réceptive
- **IAP** : Improvisation Assessment Profile
- **EMTC** : European Music Therapy Confederation

## 🔒 Sécurité et conformité

- **RGPD** : Respect de la réglementation européenne
- **Chiffrement** : Données sensibles chiffrées
- **Audit trail** : Traçabilité des accès et modifications
- **Backup** : Sauvegarde automatique des données
- **Retention** : Politique de conservation conforme

## 🤝 Contribution

1. Fork du projet
2. Création d'une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit des changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push de la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Création d'une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

- **Documentation** : [docs.synchronie.fr](https://docs.synchronie.fr)
- **Email** : support@synchronie.fr
- **Issues** : [GitHub Issues](https://github.com/votre-username/synchronie/issues)

## 🙏 Remerciements

- **OpenAI** pour l'API Whisper
- **Mistral AI** pour l'analyse intelligente
- **AMTA** pour les standards de musicothérapie
- La communauté des musicothérapeutes pour leurs retours

---

*Développé avec ❤️ pour révolutionner la musicothérapie*
