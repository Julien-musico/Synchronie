
"""
Routes pour la gestion des grilles d'évaluation (standardisées et personnalisées).
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.models.cotation import Grille

grilles_bp = Blueprint('grilles', __name__, url_prefix='/grilles')

@grilles_bp.route('/<int:grille_id>', endpoint='grille_detail')
@login_required
def grille_detail(grille_id):
    """Affiche le détail d'une grille (standardisée ou personnalisée)."""
    grille = Grille.query.get_or_404(grille_id)
    return render_template('cotation/grille_detail.html', grille=grille)

@grilles_bp.route('/', endpoint='grilles')
@login_required
def grilles():
    """Affiche toutes les grilles standardisées avec le nombre de domaines et d'indicateurs."""
    from flask_login import current_user
    # Grilles personnalisées de l'utilisateur
    grilles_user = Grille.query.filter_by(type_grille="personnalisée", user_id=current_user.id).all() if current_user.is_authenticated else []
    # Grilles publiques et standardisées
    grilles_publiques = Grille.query.filter(Grille.type_grille.in_(["standardisée", "publique"]))
    grilles_publiques = grilles_publiques.all()
    # Ajoute domaines/indicateurs pour affichage
    # Les propriétés grille.domaines sont déjà accessibles, inutile d'assigner
    return render_template('cotation/grilles.html', grilles_user=grilles_user, grilles_publiques=grilles_publiques)

@grilles_bp.route('/creer-grille-personalisee', methods=['GET', 'POST'], endpoint='creer_grille_personalisee')
@login_required
def creer_grille_personalisee():
    from app.models.cotation import Domaine, Indicateur
    if request.method == 'POST':
        nom = request.form.get('nom')
        description = request.form.get('description')
        # TODO: Traiter domaines/indicateurs, créer la grille et lier domaines/indicateurs
        flash('Grille personnalisée créée (simulation)', 'success')
        return redirect(url_for('cotation.grilles.grilles'))
    # Récupère tous les domaines et leurs indicateurs
    domaines = Domaine.query.all()
    domaines_data = []
    for domaine in domaines:
        indicateurs = Indicateur.query.join('domaine_indicateur').filter_by(domaine_id=domaine.id).all()
        domaines_data.append({
            'id': domaine.id,
            'nom': domaine.nom,
            'description': domaine.description,
            'indicateurs': [{'id': i.id, 'nom': i.nom, 'description': i.description} for i in indicateurs]
        })
    return render_template('cotation/creer_grille_personalisee.html', domaines=domaines_data)
