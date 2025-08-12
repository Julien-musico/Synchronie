"""Point d'entrée WSGI simple pour Synchronie"""
import os
import sys

# Ajouter le répertoire au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import et création de l'app
from app import create_app

application = create_app('production')
app = application

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
