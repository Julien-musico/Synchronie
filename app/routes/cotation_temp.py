"""
Routes simplifiées pour le système de cotation thérapeutique
Version temporaire sans dépendances sur les modèles manquants
"""
from flask import Blueprint, render_template, jsonify

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

@cotation_bp.route('/grilles')
def grilles():
    """Page de gestion des grilles d'évaluation - Version temporaire"""
    return render_template('cotation/grilles_temp.html')

@cotation_bp.route('/grilles/predefinies')
def grilles_predefinies():
    """API: Liste des grilles prédéfinies disponibles - Version temporaire"""
    grilles = {
        "amta_standard": {
            "nom": "AMTA - Grille Standard",
            "description": "Grille de l'Association Américaine de Musicothérapie (7 domaines, 28 indicateurs)",
            "reference_scientifique": "AMTA",
            "couleur_theme": "#e74c3c"
        },
        "imcap_nd": {
            "nom": "IMCAP-ND - Troubles Autistiques", 
            "description": "Échelle spécialisée pour troubles du spectre autistique (fiabilité 98%)",
            "reference_scientifique": "IMCAP-ND",
            "couleur_theme": "#8e44ad"
        }
    }
    return jsonify(grilles)

@cotation_bp.route('/test')
def test():
    """Route de test pour vérifier que le blueprint fonctionne"""
    return jsonify({
        'status': 'ok',
        'message': 'Blueprint cotation actif',
        'features': ['grilles_predefinies', 'interface_cotation']
    })
