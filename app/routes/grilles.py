"""Routes pour la gestion des grilles de cotation."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required  # type: ignore

from app.services.cotation_service import CotationService

grilles = Blueprint('grilles', __name__, url_prefix='/grilles')


@grilles.route('/')
@login_required  # type: ignore
def list_grilles():
    """Liste des grilles disponibles."""
    try:
        grilles_standards = CotationService.get_grilles_standards()
        grilles_personnalisees = CotationService.get_grilles_utilisateur()
        
        return render_template('grilles/list.html', 
                             grilles_standards=grilles_standards,
                             grilles_personnalisees=grilles_personnalisees)
    except Exception as e:
        flash(f"Erreur lors du chargement des grilles: {e}", 'error')
        return redirect(url_for('main.dashboard'))


@grilles.route('/nouvelle')
@login_required  # type: ignore
def new_grille():
    """Formulaire de création d'une nouvelle grille."""
    # Récupérer les templates prédéfinis
    templates = CotationService.get_grilles_predefinies()
    return render_template('grilles/form.html', grille=None, templates=templates)


@grilles.route('/create', methods=['POST'])
@login_required  # type: ignore
def create_grille():
    """Traitement de la création d'une grille."""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        if data.get('type') == 'template':
            # Création depuis un template prédéfini
            template_key = data.get('template_key')
            grille = CotationService.creer_grille_predefinie(template_key)
            if not grille:
                return jsonify({'success': False, 'message': 'Template non trouvé'}), 400
        else:
            # Création personnalisée
            nom = data.get('nom', '').strip()
            description = data.get('description', '').strip()
            domaines_data = data.get('domaines', [])
            
            if not nom:
                return jsonify({'success': False, 'message': 'Le nom est obligatoire'}), 400
            
            grille = CotationService.creer_grille_personnalisee(nom, description, domaines_data)
        
        if request.is_json:
            return jsonify({'success': True, 'grille_id': grille.id, 'message': 'Grille créée avec succès'})
        
        flash('Grille créée avec succès', 'success')
        return redirect(url_for('grilles.view_grille', grille_id=grille.id))
        
    except Exception as e:
        error_msg = f"Erreur lors de la création: {e}"
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('grilles.new_grille'))


@grilles.route('/<int:grille_id>')
@login_required  # type: ignore
def view_grille(grille_id):
    """Affichage détaillé d'une grille."""
    try:
        grille = CotationService.get_grille_by_id(grille_id)
        if not grille:
            flash('Grille non trouvée', 'error')
            return redirect(url_for('grilles.list_grilles'))
        
        return render_template('grilles/detail.html', grille=grille)
    except Exception as e:
        flash(f"Erreur lors du chargement: {e}", 'error')
        return redirect(url_for('grilles.list_grilles'))


@grilles.route('/<int:grille_id>/modifier')
@login_required  # type: ignore
def edit_grille(grille_id):
    """Formulaire de modification d'une grille."""
    try:
        grille = CotationService.get_grille_by_id(grille_id)
        if not grille:
            flash('Grille non trouvée', 'error')
            return redirect(url_for('grilles.list_grilles'))
        
        templates = CotationService.get_grilles_predefinies()
        return render_template('grilles/form.html', grille=grille, templates=templates)
    except Exception as e:
        flash(f"Erreur lors du chargement: {e}", 'error')
        return redirect(url_for('grilles.list_grilles'))


@grilles.route('/<int:grille_id>/update', methods=['POST'])
@login_required  # type: ignore
def update_grille(grille_id):
    """Traitement de la modification d'une grille."""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        nom = data.get('nom', '').strip()
        description = data.get('description', '').strip()
        domaines_data = data.get('domaines', [])
        
        grille = CotationService.update_grille_complete(grille_id, nom, description, domaines_data)
        if not grille:
            error_msg = "Grille non trouvée ou non autorisée"
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 404
            flash(error_msg, 'error')
            return redirect(url_for('grilles.list_grilles'))
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Grille mise à jour avec succès'})
        
        flash('Grille mise à jour avec succès', 'success')
        return redirect(url_for('grilles.view_grille', grille_id=grille.id))
        
    except Exception as e:
        error_msg = f"Erreur lors de la mise à jour: {e}"
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('grilles.edit_grille', grille_id=grille_id))


@grilles.route('/<int:grille_id>/copier', methods=['POST'])
@login_required  # type: ignore
def copy_grille(grille_id):
    """Copie d'une grille existante."""
    try:
        grille = CotationService.copier_grille(grille_id)
        if not grille:
            return jsonify({'success': False, 'message': 'Grille non trouvée ou non accessible'}), 404
        
        return jsonify({'success': True, 'grille_id': grille.id, 'message': 'Grille copiée avec succès'})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Erreur lors de la copie: {e}"}), 500


@grilles.route('/<int:grille_id>/supprimer', methods=['POST'])
@login_required  # type: ignore
def delete_grille(grille_id):
    """Suppression d'une grille."""
    try:
        success = CotationService.supprimer_grille(grille_id)
        if not success:
            return jsonify({'success': False, 'message': 'Grille non trouvée ou non autorisée'}), 404
        
        return jsonify({'success': True, 'message': 'Grille supprimée avec succès'})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Erreur lors de la suppression: {e}"}), 500


@grilles.route('/api/templates')
@login_required  # type: ignore
def api_templates():
    """API pour récupérer les templates de grilles."""
    try:
        templates = CotationService.get_grilles_predefinies()
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Erreur: {e}"}), 500


@grilles.route('/api/disponibles')
@login_required  # type: ignore
def api_grilles_disponibles():
    """API pour récupérer les grilles disponibles pour un patient."""
    try:
        grilles_standards = CotationService.get_grilles_standards()
        grilles_personnalisees = CotationService.get_grilles_utilisateur()
        
        return jsonify({
            'success': True,
            'grilles': {
                'standards': [{'id': g.id, 'nom': g.nom, 'description': g.description} for g in grilles_standards],
                'personnalisees': [{'id': g.id, 'nom': g.nom, 'description': g.description} for g in grilles_personnalisees]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f"Erreur: {e}"}), 500
