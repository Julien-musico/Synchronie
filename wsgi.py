"""
Point d'entrée WSGI pour Synchronie
Utilisé par Gunicorn pour démarrer l'application
"""

import os
import sys

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration environnement
os.environ.setdefault('FLASK_ENV', 'production')

try:
    from app import create_app
    
    # Créer l'application Flask
    application = create_app('production')
    
    # Pour compatibilité avec Gunicorn
    app = application
    
    if __name__ == "__main__":
        # Pour tests locaux uniquement
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
        
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("🔍 Structure des fichiers:")
    import os
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")
    sys.exit(1)
