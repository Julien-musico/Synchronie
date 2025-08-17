
"""
Routes pour la gestion des grilles d'évaluation (standardisées et personnalisées).
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app.models.cotation import Grille, Domaine, Indicateur, GrilleDomaine, DomaineIndicateur

grilles_bp = Blueprint('grilles', __name__, url_prefix='/grilles')

# --- Nouvelle route pour le catalogue domaines/indicateurs ---
@grilles_bp.route('/catalogue_domaines_indicateurs', methods=['GET'])
def catalogue_domaines_indicateurs():
    """
    Retourne la liste des domaines et pour chaque domaine, la liste des indicateurs associés.
    Format : [{id, nom, indicateurs: [{id, nom}, ...]}, ...]
    """
    from app.models.cotation import Domaine, Indicateur, DomaineIndicateur
    domaines = Domaine.query.all()
    result = []
    for domaine in domaines:
        indicateurs = Indicateur.query.join(DomaineIndicateur).filter(DomaineIndicateur.domaine_id == domaine.id).all()
        result.append({
            'id': domaine.id,
            'nom': domaine.nom,
            'indicateurs': [{'id': i.id, 'nom': i.nom} for i in indicateurs]
        })
    return jsonify(result)

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
    # Les modèles sont déjà importés en haut
    if request.method == 'POST':
        nom = request.form.get('nom')
        description = request.form.get('description')
        domaines_data = request.form.get('domaines')
        import json
        if domaines_data:
            domaines_data = json.loads(domaines_data)
        else:
            domaines_data = []
        from app import db
        from flask_login import current_user
        grille = Grille(nom=nom, description=description, type_grille='personnalisée', user_id=current_user.id)
        db.session.add(grille)
        db.session.flush()
        for domaine_info in domaines_data:
            domaine = Domaine.query.filter_by(nom=domaine_info['nom']).first()
            if not domaine:
                domaine = Domaine(nom=domaine_info['nom'])
                db.session.add(domaine)
                db.session.flush()
            # Vérifier si le lien existe déjà
            if not GrilleDomaine.query.filter_by(grille_id=grille.id, domaine_id=domaine.id).first():
                grille_domaine = GrilleDomaine(grille_id=grille.id, domaine_id=domaine.id)
                db.session.add(grille_domaine)
            for indicateur_nom in domaine_info['indicateurs']:
                indicateur = Indicateur.query.filter_by(nom=indicateur_nom).first()
                if not indicateur:
                    indicateur = Indicateur(nom=indicateur_nom)
                    db.session.add(indicateur)
                    db.session.flush()
                # Vérifier si le lien existe déjà
                if not DomaineIndicateur.query.filter_by(domaine_id=domaine.id, indicateur_id=indicateur.id).first():
                    domaine_indicateur = DomaineIndicateur(domaine_id=domaine.id, indicateur_id=indicateur.id)
                    db.session.add(domaine_indicateur)
        db.session.commit()
        flash('Grille personnalisée créée avec succès.', 'success')
        return redirect(url_for('cotation.grilles.grilles'))
    # Récupère tous les domaines et leurs indicateurs
    domaines = Domaine.query.all()
    domaines_data = []
    for domaine in domaines:
        indicateurs = Indicateur.query.join(DomaineIndicateur, Indicateur.id == DomaineIndicateur.indicateur_id).filter(DomaineIndicateur.domaine_id == domaine.id).all()
        domaines_data.append({
            'id': domaine.id,
            'nom': domaine.nom,
            'description': domaine.description,
            'indicateurs': [{'id': i.id, 'nom': i.nom, 'description': i.description} for i in indicateurs]
        })
    return render_template('cotation/creer_grille_personalisee.html', domaines=domaines_data)
