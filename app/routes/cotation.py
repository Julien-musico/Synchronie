"""
Utilitaires d'accès utilisateur pour factoriser la vérification d'ownership.
"""

# -------------------- IMPORTS -------------------- #

import json
import os

from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.models import Patient, Seance, db
from app.models.cotation import CotationSeance, GrilleEvaluation
from app.services.analytics_service import AnalyticsService
from app.services.cotation_service import CotationService

 # Blueprint definition must come before any route decorators
cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

# Route for custom grille detail (for non-standard grilles)
@cotation_bp.route('/grille/<int:grille_id>')
@login_required
def grille_detail(grille_id):
    """Affiche le détail d'une grille personnalisée (non standard)."""
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    # Vérifier l'accès: grille doit appartenir à l'utilisateur ou être publique
    if not grille.publique and grille.user_id != current_user.id:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('cotation.grilles'))
    return render_template('cotation/grille_detail.html', grille=grille)

def user_owns_patient(patient):
    """Vérifie que le patient appartient à l'utilisateur courant."""
    return patient.user_id == current_user.id

def user_owns_grille(grille):
    """Vérifie que la grille appartient à l'utilisateur courant ou est publique."""
    return grille.publique or grille.user_id == current_user.id
# Route GET pour afficher le formulaire de création de grille personnalisée
@cotation_bp.route('/grilles/creer-personnalisee', methods=['GET'])
@login_required
def creer_grille_personnalisee_form():
    """Affiche le formulaire de création d'une grille personnalisée."""
    return render_template('cotation/creer_grille_personnalisee.html')
"""
Routes pour le système de cotation thérapeutique
"""

@cotation_bp.route('/analyses')
@login_required
def analyses_overview():  # type: ignore[no-untyped-def]
    """Page d'analyse (vue globale)."""
    return render_template('analyses/overview.html')

def charger_grilles_standards():
    """Charge toutes les grilles JSON du dossier grilles_standard et les retourne sous forme de liste."""
    grilles = []
    dossier = os.path.join(os.path.dirname(__file__), '../../data/grilles_standard')
    for nom_fichier in os.listdir(dossier):
        if nom_fichier.endswith('.json'):
            chemin = os.path.join(dossier, nom_fichier)
            try:
                with open(chemin, encoding='utf-8') as f:
                    data = json.load(f)
                grilles.append({
                    'nom': data.get('nom', nom_fichier.replace('.json','').upper()),
                    'description': data.get('description', ''),
                    'domaines': data.get('domaines', []),
                    'reference_scientifique': data.get('reference_scientifique', nom_fichier.replace('.json','').upper()),
                    'versions': [data],
                    'id': f"std-{nom_fichier}",
                    'publique': True
                })
            except Exception as e:
                import traceback
                print(f"[GRILLES STANDARD] Erreur chargement {nom_fichier}: {e}")
                traceback.print_exc()
    print(f"[GRILLES STANDARD] {len(grilles)} grilles chargées: {[g['nom'] for g in grilles]}")
    return grilles

@cotation_bp.route('/grilles')
@login_required
def grilles():  # type: ignore[no-untyped-def]
    """Page de gestion des grilles d'évaluation"""
    from flask import current_app
    try:
        grilles_user = GrilleEvaluation.query.filter_by(
            user_id=current_user.id,
            active=True
        ).all()
        grilles_publiques = GrilleEvaluation.query.filter_by(
            publique=True,
            active=True
        ).all()
        # Ajout des grilles standards JSON
        grilles_standards = charger_grilles_standards()
        grilles_publiques = list(grilles_publiques) + grilles_standards
        print("DEBUG grilles_user:", grilles_user)
        print("DEBUG grilles_publiques:", grilles_publiques)
        return render_template('cotation/grilles.html',
                               grilles_user=grilles_user,
                               grilles_publiques=grilles_publiques)
    except Exception:  # pragma: no cover
        current_app.logger.exception("Erreur chargement grilles")
        flash('Erreur interne chargement des grilles', 'error')
        return render_template('cotation/grilles.html', grilles_user=[], grilles_publiques=[]), 500

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
    data = request.get_json(silent=True) or {}
    type_grille = data.get('type_grille')
    
    try:
        if not type_grille:
            return jsonify({'success': False, 'error': 'Type de grille requis'}), 400
        grille = CotationService.creer_grille_predefinie(type_grille)
        if not grille:
            return jsonify({'success': False, 'error': 'Type de grille inconnu'}), 400
        # Assigner à l'utilisateur actuel
        grille.user_id = current_user.id
        grille.publique = False
        db.session.commit()
        return jsonify({
            'success': True,
            'grille_id': grille.id,
            'nom': grille.nom
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cotation_bp.route('/seances-a-coter')
@login_required
def seances_a_coter():
    """Page listant les séances disponibles pour cotation"""
    # Récupérer toutes les séances de l'utilisateur via la relation patient
    seances = db.session.query(Seance).join(Patient).filter(
        Patient.user_id == current_user.id
    ).order_by(Seance.date_seance.desc()).all()
    
    # Enrichir avec info cotation
    seances_info = []
    for seance in seances:
        cotations = CotationSeance.query.filter_by(seance_id=seance.id).all()
        seances_info.append({
            'seance': seance,
            'nb_cotations': len(cotations),
            'derniere_cotation': cotations[-1] if cotations else None
        })
    
    return render_template('cotation/seances_a_coter.html', seances_info=seances_info)

@cotation_bp.route('/seance/<int:seance_id>/coter')
@login_required
def interface_cotation(seance_id):
    """Interface visuelle de cotation d'une séance"""
    try:
        seance = Seance.query.get_or_404(seance_id)
        
        # Vérifier que l'utilisateur a accès à cette séance
        if seance.patient.user_id != current_user.id:
            flash('Accès non autorisé', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Grilles disponibles pour l'utilisateur - version robuste
        try:
            grilles = GrilleEvaluation.query.filter(
                db.or_(
                    GrilleEvaluation.user_id == current_user.id,
                    GrilleEvaluation.publique.is_(True)
                ),
                GrilleEvaluation.active.is_(True)
            ).all()
        except Exception:
            # Fallback si les colonnes publique/active n'existent pas encore
            grilles = GrilleEvaluation.query.filter(
                db.or_(
                    GrilleEvaluation.user_id == current_user.id,
                    GrilleEvaluation.user_id.is_(None)
                )
            ).all()
        
        # Cotations existantes pour cette séance
        cotations_existantes = CotationSeance.query.filter_by(seance_id=seance_id).all()
        
        return render_template('cotation/interface_cotation_clean.html',
                             seance=seance,
                             grilles=grilles,
                             cotations_existantes=cotations_existantes)
    except Exception as e:
        flash(f'Erreur lors du chargement de l\'interface de cotation: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@cotation_bp.route('/grille/<int:grille_id>/preview')
@login_required
def preview_grille(grille_id):
    """API: Aperçu d'une grille avec tous ses domaines et indicateurs"""
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    
    # Vérifier l'accès
    if not grille.publique and grille.user_id != current_user.id:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    return jsonify({
        'id': grille.id,
        'nom': grille.nom,
        'description': grille.description,
        'domaines': grille.domaines,
        'couleur_theme': grille.domaines[0].get('couleur', '#3498db') if grille.domaines else '#3498db'
    })

@cotation_bp.route('/grille/<int:grille_id>/domaines')
@login_required
def api_grille_domaines(grille_id: int) -> 'Response':
    """API: Domaines et indicateurs d'une grille (remplace l'ancienne route /grilles/api/<id>/domaines)."""
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    # Vérifier l'accès: publique ou appartenant à l'utilisateur
    if not grille.publique and grille.user_id != current_user.id:
        response = jsonify({'success': False, 'message': 'Accès non autorisé'})
        response.status_code = 403
        return response

    # Normaliser les domaines/indicateurs et injecter des IDs si absents
    domaines_data = []
    try:
        raw_domaines = grille.domaines or []
        for d_idx, domaine in enumerate(raw_domaines):
            dom_id = domaine.get('id') or f"d{d_idx+1}"
            indicateurs_data = []
            for i_idx, indicateur in enumerate(domaine.get('indicateurs', [])):
                ind_id = indicateur.get('id') or f"{dom_id}_i{i_idx+1}"
                indicateur['id'] = ind_id
                indicateurs_data.append(indicateur)
            domaine_data = dict(domaine)
            domaine_data['id'] = dom_id
            domaine_data['indicateurs'] = indicateurs_data
            domaines_data.append(domaine_data)
        return jsonify({'domaines': domaines_data})
    except Exception as e:
        response = jsonify({'success': False, 'message': f'Erreur: {str(e)}'})
        response.status_code = 500
        return response

@cotation_bp.route('/grille-standard/<grille_id>')
@login_required
def grille_standard_detail(grille_id):
    """Affiche le détail d'une grille standard (JSON)"""
    import os
    chemin = os.path.join(os.path.dirname(__file__), '../../data/grilles_standard', grille_id)
    if not os.path.exists(chemin):
        flash('Grille standard introuvable', 'error')
        return redirect(url_for('cotation.grilles'))
    with open(chemin, encoding='utf-8') as f:
        grille = json.load(f)
        # Pour compatibilité avec le template
        grille['id'] = f'std-{grille_id}'
        grille['publique'] = True
        grille['versions'] = [grille]
    return render_template('cotation/grille_detail.html', grille=grille)

@cotation_bp.route('/grille/<int:grille_id>/editer-domaines')
@login_required
def editer_domaines_page(grille_id):  # type: ignore[no-untyped-def]
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    if not user_owns_grille(grille):
        flash('Accès non autorisé', 'error')
        return redirect(url_for('cotation.grilles'))
    # Passer domaines JSON pour initialisation
    return render_template('cotation/editer_domaines.html', grille=grille, domaines_json=json.dumps(grille.domaines))

# ---------------------- CRUD additionnel pour les grilles ---------------------- #
@cotation_bp.route('/grilles/personnalisee', methods=['POST'])
@login_required
def creer_grille_personnalisee_route():  # type: ignore[no-untyped-def]
    data = request.json or {}
    try:
        grille = CotationService.creer_grille_personnalisee(
            nom=data.get('nom', 'Nouvelle grille'),
            description=data.get('description', ''),
            domaines=data.get('domaines', [])
        )
        # Affecter l'utilisateur courant et rendre la grille privée
        grille.user_id = current_user.id
        grille.publique = False
        db.session.commit()
        return jsonify({'success': True, 'grille_id': grille.id})
    except Exception as e:  # pragma: no cover
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@cotation_bp.route('/grille/<int:grille_id>/copier', methods=['POST'])
@login_required
def copier_grille_route(grille_id):  # type: ignore[no-untyped-def]
    copie = CotationService.copier_grille(grille_id)
    if not copie:
        return jsonify({'success': False, 'error': 'Impossible de copier la grille'}), 400
    return jsonify({'success': True, 'grille_id': copie.id})

@cotation_bp.route('/grille/<int:grille_id>', methods=['PATCH'])
@login_required
def editer_grille_route(grille_id):  # type: ignore[no-untyped-def]
    data = request.json or {}
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    if not user_owns_grille(grille):
        return jsonify({'success': False, 'error': 'Modification non autorisée'}), 403
    # Modification via service
    grille = CotationService.editer_grille(grille_id, data.get('nom'), data.get('description'))
    return jsonify({'success': True})

@cotation_bp.route('/grille/<int:grille_id>/domaines', methods=['PUT'])
@login_required
def update_domaines_route(grille_id):  # type: ignore[no-untyped-def]
    data = request.json or {}
    domaines = data.get('domaines', [])
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    if not user_owns_grille(grille):
        return jsonify({'success': False, 'error': 'Mise à jour non autorisée'}), 403
    grille = CotationService.update_grille_domaines(grille_id, domaines)
    return jsonify({'success': True})

@cotation_bp.route('/grille/<int:grille_id>', methods=['DELETE'])
@login_required
def supprimer_grille_route(grille_id):  # type: ignore[no-untyped-def]
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    if not user_owns_grille(grille):
        return jsonify({'success': False, 'error': 'Suppression non autorisée'}), 403
    CotationService.supprimer_grille(grille_id)
    return jsonify({'success': True})

@cotation_bp.route('/seance/<int:seance_id>/sauvegarder', methods=['POST'])
@login_required
def sauvegarder_cotation(seance_id):
    """Sauvegarde une cotation complète"""
    seance = Seance.query.get_or_404(seance_id)
    # Vérification ownership patient factorisée
    if not user_owns_patient(seance.patient):
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    try:
        data = request.get_json(silent=True) or {}
        grille_id = data.get('grille_id')
        scores = data.get('scores', {})
        observations = data.get('observations', '')
        
        # Vérifier si une cotation existe déjà
        cotation_existante = CotationSeance.query.filter_by(
            seance_id=seance_id,
            grille_id=grille_id
        ).first()
        
        if cotation_existante:
            cotation_existante.scores_detailles = json.dumps(scores)
            cotation_existante.observations_cotation = observations
            grille = GrilleEvaluation.query.get(grille_id)
            if not grille:
                return jsonify({'success': False, 'error': 'Grille introuvable'}), 404
            score_global, score_max, pourcentage = CotationService.calculer_score_global(scores, grille)
            cotation_existante.score_global = score_global
            cotation_existante.score_max_possible = score_max
            cotation_existante.pourcentage_reussite = pourcentage
            cotation = cotation_existante
        else:
            if grille_id is None:
                return jsonify({'success': False, 'error': 'Grille requise'}), 400
            cotation = CotationService.creer_cotation(
                seance_id=seance_id,
                grille_id=int(grille_id),
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
    if not user_owns_patient(patient):
        return jsonify({'error': 'Accès non autorisé'}), 403
    evolution = CotationService.get_evolution_patient(patient_id, grille_id)
    grille = GrilleEvaluation.query.get(grille_id)
    grille_nom = grille.nom if grille else 'Grille'
    return jsonify({
        'patient_nom': f"{patient.prenom} {patient.nom}",
        'grille_nom': grille_nom,
        'evolution': evolution
    })

@cotation_bp.route('/seance/<int:seance_id>/cotations')
@login_required
def cotations_seance(seance_id):
    """API: Toutes les cotations d'une séance"""
    seance = Seance.query.get_or_404(seance_id)
    if not user_owns_patient(seance.patient):
        return jsonify({'error': 'Accès non autorisé'}), 403
    try:
        seance = Seance.query.get_or_404(seance_id)
        # Vérifier que l'utilisateur a accès à cette séance
        if seance.patient.user_id != current_user.id:
            flash('Accès non autorisé', 'error')
            return redirect(url_for('main.dashboard'))
        # Grilles disponibles pour l'utilisateur - version robuste
        try:
            grilles = GrilleEvaluation.query.filter(
                db.or_(
                    GrilleEvaluation.user_id == current_user.id,
                    GrilleEvaluation.publique.is_(True)
                ),
                GrilleEvaluation.active.is_(True)
            ).all()
        except Exception:
            # Fallback si les colonnes publique/active n'existent pas encore
            grilles = GrilleEvaluation.query.filter(
                db.or_(
                    GrilleEvaluation.user_id == current_user.id,
                    GrilleEvaluation.user_id.is_(None)
                )
            ).all()
        # Cotations existantes pour cette séance
        cotations_existantes = CotationSeance.query.filter_by(seance_id=seance_id).all()
        return render_template('cotation/interface_cotation_clean.html',
            seance=seance,
            grilles=grilles,
            cotations_existantes=cotations_existantes)
    except Exception as e:
        flash(f'Erreur lors du chargement de l\'interface de cotation: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))
@login_required
def analytics_activite_hebdo():
    """API: Activité hebdomadaire (8 dernières semaines)."""
    data = AnalyticsService.activite_hebdomadaire(current_user.id, 8)
    return jsonify(data)

@cotation_bp.route('/analytics/scores-grilles')
@login_required
def analytics_scores_grilles():
    """API: Scores moyens par grille (Top 8)."""
    data = AnalyticsService.scores_moyens_par_grille(current_user.id, 8)
    return jsonify({'items': data})

@cotation_bp.route('/analytics/patient/<int:patient_id>/grille/<int:grille_id>/evolution')
@login_required
def evolution_detaillee(patient_id, grille_id):
    """API: Évolution détaillée d'un patient pour une grille"""
    # Vérifier ownership du patient
    patient = Patient.query.get_or_404(patient_id)
    if not user_owns_patient(patient):
        return jsonify({'error': 'Accès non autorisé'}), 403
    evolution = AnalyticsService.evolution_patient_detaillee(patient_id, grille_id)
    return jsonify(evolution)

@cotation_bp.route('/analytics/patients-risque')
@login_required 
def patients_risque():
    """API: Patients nécessitant une attention particulière"""
    seuil = request.args.get('seuil', 40.0, type=float)
    # Les patients à risque sont toujours filtrés par ownership utilisateur
    patients = AnalyticsService.patients_a_risque(current_user.id, seuil)
    return jsonify({'patients_risque': patients, 'seuil_utilise': seuil})

@cotation_bp.route('/analytics/rapport-mensuel/<int:annee>/<int:mois>')
@login_required
def rapport_mensuel(annee, mois):
    """API: Rapport d'activité mensuel"""
    if not (1 <= mois <= 12) or not (2020 <= annee <= 2030):
        return jsonify({'error': 'Période invalide'}), 400
    # Rapport filtré par ownership utilisateur
    rapport = AnalyticsService.rapport_activite_mensuel(current_user.id, annee, mois)
    return jsonify(rapport)


@cotation_bp.route('/api/cotation/save', methods=['POST'])
@login_required
def api_save_cotation():
    """API pour sauvegarder une cotation de séance."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Données manquantes'}), 400
        
        seance_id = data.get('seance_id')
        grille_id = data.get('grille_id')
        scores = data.get('scores', {})
        observations = data.get('observations', '')
        
        if not seance_id or not grille_id:
            return jsonify({'success': False, 'message': 'Séance et grille requises'}), 400
        
        # Vérifier que la séance existe et appartient à l'utilisateur
        seance = Seance.query.get(seance_id)
        if not seance or not user_owns_patient(seance.patient):
            return jsonify({'success': False, 'message': 'Séance non trouvée ou accès refusé'}), 404

        # Sauvegarder les scores
        success = CotationService.sauvegarder_cotation_seance(
            seance_id=seance_id,
            grille_id=grille_id,
            scores=scores,
            observations=observations
        )

        if success:
            return jsonify({'success': True, 'message': 'Cotation sauvegardée avec succès'})
        return jsonify({'success': False, 'message': 'Erreur lors de la sauvegarde'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500
