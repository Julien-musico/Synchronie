# 🚀 Guide de déploiement Synchronie sur Render

## Étapes de déploiement

### 1. **Préparation du repository**
```bash
git add .
git commit -m "Initial Synchronie setup for Render"
git push origin main
```

### 2. **Configuration sur Render.com**

#### A. Créer un nouveau Web Service
1. Allez sur [render.com](https://render.com)
2. Connectez votre repository GitHub `Synchronie`
3. Choisissez "Web Service"

#### B. Configuration du service
- **Name**: `synchronie-app`
- **Environment**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
- **Branch**: `main`

#### C. Variables d'environnement à configurer
```env
SECRET_KEY=your-super-secret-key-generate-a-new-one
FLASK_ENV=production
OPENAI_API_KEY=sk-your-openai-key
MISTRAL_API_KEY=your-mistral-api-key
ADMIN_EMAIL=votre-email@example.com
ADMIN_PASSWORD=VotreMotDePasseSecurise123!
```

### 3. **Ajouter PostgreSQL**
1. Dans le dashboard Render, cliquez "New" → "PostgreSQL"
2. Nommez la base : `synchronie-db`
3. La variable `DATABASE_URL` sera automatiquement liée

### 4. **Déploiement automatique**
- Chaque push sur `main` déclenchera un redéploiement
- Les logs sont visibles en temps réel dans le dashboard

## 🔧 **Debugging via les logs Render**

### Accès aux logs
1. Dashboard Render → Votre service → Onglet "Logs"
2. Logs en temps réel pendant le déploiement
3. Logs d'application en continu

### Types de logs utiles

#### Logs de déploiement
```
==> Building...
📦 Installation des dépendances Python...
🗄️ Mise à jour de la base de données...
✅ Déploiement terminé avec succès !
```

#### Logs d'application
```python
# Dans votre code, ajoutez des logs :
import logging
logger = logging.getLogger(__name__)

# Exemple dans les services
logger.info(f"Transcription démarrée pour fichier: {filename}")
logger.error(f"Erreur IA: {str(e)}")
```

#### Logs de requêtes
```
127.0.0.1 - - [12/Aug/2025 14:30:45] "GET /patients HTTP/1.1" 200 -
127.0.0.1 - - [12/Aug/2025 14:30:50] "POST /sessions/upload HTTP/1.1" 500 -
```

### Debug des erreurs communes

#### 1. Erreur de base de données
```bash
# Log typique
sqlalchemy.exc.OperationalError: could not connect to server

# Solution : Vérifier DATABASE_URL dans les variables d'environnement
```

#### 2. Erreur API IA
```bash
# Log typique  
openai.error.AuthenticationError: Invalid API key

# Solution : Vérifier OPENAI_API_KEY
```

#### 3. Erreur de fichiers uploadés
```bash
# Log typique
FileNotFoundError: No such file or directory: '/uploads/audio.mp3'

# Solution : Utiliser /tmp/uploads sur Render
```

## 🎯 **Workflow de développement recommandé**

### 1. **Développement par feature**
```bash
# Créer une branche pour chaque fonctionnalité
git checkout -b feature/transcription-audio
# ... développement ...
git add .
git commit -m "Add audio transcription service"
git push origin feature/transcription-audio
```

### 2. **Test sur branche de staging**
- Créer un service Render séparé pour le staging
- Connecter la branche `develop`
- Tester avant de merger sur `main`

### 3. **Déploiement en production**
```bash
git checkout main
git merge feature/transcription-audio
git push origin main
# → Déploiement automatique sur Render
```

## 📊 **Monitoring et maintenance**

### Métriques Render
- CPU et RAM usage
- Response time
- Erreur rate
- Database connections

### Logs structurés recommandés
```python
# Dans app/utils/logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_session_processing(self, patient_id, session_id, status, details=None):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'session_processing',
            'patient_id': patient_id,
            'session_id': session_id,
            'status': status,
            'details': details
        }
        self.logger.info(json.dumps(log_data))

# Usage
logger = StructuredLogger('synchronie.sessions')
logger.log_session_processing(123, 456, 'transcription_started')
```

## ⚡ **Optimisations pour Render**

### Performance
```python
# config.py - Configuration optimisée pour Render
class ProductionConfig(Config):
    # Pool de connexions DB optimisé
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Cache des templates
    TEMPLATES_AUTO_RELOAD = False
    
    # Compression
    COMPRESS_ALGORITHM = 'gzip'
```

### Gestion des fichiers
```python
# Utiliser le stockage temporaire de Render efficacement
import tempfile
import os

def handle_audio_upload(file):
    # Stocker temporairement
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        file.save(tmp.name)
        
        # Traiter le fichier
        result = process_audio(tmp.name)
        
        # Nettoyer
        os.unlink(tmp.name)
        
        return result
```

## 🆘 **Support et dépannage**

### Erreurs fréquentes et solutions

1. **Build failed** → Vérifier `requirements.txt` et `runtime.txt`
2. **Database connection error** → Vérifier que PostgreSQL est bien lié
3. **API timeout** → Augmenter les timeouts dans `Procfile`
4. **Memory errors** → Optimiser le traitement des fichiers audio

### Contacts utiles
- Documentation Render : [render.com/docs](https://render.com/docs)
- Support Render : Via dashboard
- Logs Synchronie : Dashboard → Service → Logs
