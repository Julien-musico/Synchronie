"""
Routes pour le système de cotation thérapeutique
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
try:
    from flask_login import login_required, current_user  # type: ignore
except ImportError:  # fallback pour analyse statique si non installé
    def login_required(func):  # type: ignore
        return func
    class _User:  # type: ignore
        id: int = 0
    current_user = _User()  # type: ignore
from app.models import db, Seance, Patient
from app.models.cotation import GrilleEvaluation, CotationSeance
from app.services.cotation_service import CotationService
import json

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

@cotation_bp.route('/grilles')
@login_required
def grilles():  # type: ignore[no-untyped-def]
    """Page de gestion des grilles d'évaluation"""
    grilles_user = GrilleEvaluation.query.filter_by(
        musicotherapeute_id=current_user.id,
        active=True
    ).all()
    
    grilles_publiques = GrilleEvaluation.query.filter_by(
        publique=True,
        active=True
    ).all()
    
    return render_template('cotation/grilles.html',
                         grilles_user=grilles_user,
                         grilles_publiques=grilles_publiques)

@cotation_bp.route('/grilles/predefinies')
@login_required
def grilles_predefinies():  # type: ignore[no-untyped-def]
    """API: Liste des grilles prédéfinies disponibles"""
    grilles = CotationService.get_grilles_predefinies()
    return jsonify(grilles)

@cotation_bp.route('/grilles/creer-predefinee', methods=['POST'])
@login_required
def creer_grille_predefinee():
    """Crée une grille prédéfinie pour l'utilisateur"""
    type_grille = request.json.get('type_grille')
    
    try:
        grille = CotationService.creer_grille_predefinee(type_grille)
        if grille:
            # Assigner à l'utilisateur actuel
            grille.musicotherapeute_id = current_user.id
            grille.publique = False
            db.session.commit()
            
            return jsonify({
                'success': True,
                'grille_id': grille.id,
                'nom': grille.nom
            })
        else:
            return jsonify({'success': False, 'error': 'Type de grille inconnu'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cotation_bp.route('/seance/<int:seance_id>/coter')
@login_required
def interface_cotation(seance_id):
    """Interface visuelle de cotation d'une séance"""
    seance = Seance.query.get_or_404(seance_id)
    
    # Vérifier que l'utilisateur a accès à cette séance
    if seance.patient.musicotherapeute_id != current_user.id:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
    
    # Grilles disponibles pour l'utilisateur
    grilles = GrilleEvaluation.query.filter(
        db.or_(
            GrilleEvaluation.musicotherapeute_id == current_user.id,
            GrilleEvaluation.publique.is_(True)
        ),
        GrilleEvaluation.active.is_(True)
    ).all()
    
    # Cotations existantes pour cette séance
    cotations_existantes = CotationSeance.query.filter_by(seance_id=seance_id).all()
    
    return render_template('cotation/interface_cotation.html',
                         seance=seance,
                         grilles=grilles,
                         cotations_existantes=cotations_existantes)

@cotation_bp.route('/grille/<int:grille_id>/preview')
@login_required
def preview_grille(grille_id):
    """API: Aperçu d'une grille avec tous ses domaines et indicateurs"""
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    
    # Vérifier l'accès
    if not grille.publique and grille.musicotherapeute_id != current_user.id:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    return jsonify({
        'id': grille.id,
        'nom': grille.nom,
        'description': grille.description,
        'domaines': grille.domaines,
        'couleur_theme': grille.domaines[0].get('couleur', '#3498db') if grille.domaines else '#3498db'
    })

@cotation_bp.route('/seance/<int:seance_id>/sauvegarder', methods=['POST'])
@login_required
def sauvegarder_cotation(seance_id):
    """Sauvegarde une cotation complète"""
    seance = Seance.query.get_or_404(seance_id)
    
    if seance.patient.musicotherapeute_id != current_user.id:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    
    try:
        data = request.json
        grille_id = data.get('grille_id')
        scores = data.get('scores', {})
        observations = data.get('observations', '')
        
        # Vérifier si une cotation existe déjà
        cotation_existante = CotationSeance.query.filter_by(
            seance_id=seance_id,
            grille_id=grille_id
        ).first()
        
        if cotation_existante:
            # Mettre à jour
            cotation_existante.scores_detailles = json.dumps(scores)
            cotation_existante.observations_cotation = observations
            
            # Recalculer les scores
            grille = GrilleEvaluation.query.get(grille_id)
            score_global, score_max, pourcentage = CotationService.calculer_score_global(scores, grille)
            cotation_existante.score_global = score_global
            cotation_existante.score_max_possible = score_max
            cotation_existante.pourcentage_reussite = pourcentage
            
            cotation = cotation_existante
        else:
            # Créer nouvelle cotation
            cotation = CotationService.creer_cotation(
                seance_id=seance_id,
                grille_id=grille_id,
                scores=scores,
                observations=observations
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cotation_id': cotation.id,
            'score_global': cotation.score_global,
            'pourcentage': round(cotation.pourcentage_reussite, 1)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cotation_bp.route('/patient/<int:patient_id>/evolution/<int:grille_id>')
@login_required
def evolution_patient(patient_id, grille_id):
    """API: Données d'évolution d'un patient pour une grille donnée"""
    patient = Patient.query.get_or_404(patient_id)
    
    if patient.musicotherapeute_id != current_user.id:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    evolution = CotationService.get_evolution_patient(patient_id, grille_id)
    
    return jsonify({
        'patient_nom': f"{patient.prenom} {patient.nom}",
        'grille_nom': GrilleEvaluation.query.get(grille_id).nom,
        'evolution': evolution
    })

@cotation_bp.route('/seance/<int:seance_id>/cotations')
@login_required
def cotations_seance(seance_id):
    """API: Toutes les cotations d'une séance"""
    seance = Seance.query.get_or_404(seance_id)
    
    if seance.patient.musicotherapeute_id != current_user.id:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    cotations = CotationSeance.query.filter_by(seance_id=seance_id).all()
    
    result = []
    for cotation in cotations:
        result.append({
            'id': cotation.id,
            'grille_nom': cotation.grille.nom,
            'score_global': cotation.score_global,
            'pourcentage': round(cotation.pourcentage_reussite, 1),
            'scores_detailles': cotation.scores,
            'observations': cotation.observations_cotation,
            'date_cotation': cotation.date_creation.isoformat()
        })
    
    return jsonify(result)
