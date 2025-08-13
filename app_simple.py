"""
Point d'entrée simple pour Gunicorn en cas de problème avec la structure MVC
"""
import os

from flask import Flask

# Créer une application Flask simple
app = Flask(__name__)

# Configuration de base
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎵 Synchronie</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #667eea; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Synchronie</h1>
            <h2>Application en cours de configuration</h2>
            <p>L'application principale est en cours de mise en place.</p>
            <p>Cette page temporaire confirme que le déploiement fonctionne.</p>
            <hr>
            <p><strong>Status:</strong> ✅ Déployé avec succès</p>
            <p><strong>Version:</strong> 1.0.1 - Correction déploiement</p>
        </div>
    </body>
    </html>
    '''

@app.route('/api/health')
def health():
    return {
        'status': 'healthy',
        'message': 'Synchronie API is running',
        'version': '1.0.1'
    }

if __name__ == '__main__':
    app.run(debug=True)
