"""
Point d'entrée principal pour l'application Synchronie
"""
import os
from app import create_app

# Création de l'application avec la configuration appropriée
config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    app.run(debug=True)
