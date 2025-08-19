from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.cotation import GrilleEvaluation, Domaine, Indicateur
from flask_login import current_user

from .seances import seances_bp
from .analytics import analytics_bp

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

@cotation_bp.route('/grilles', methods=['GET'])
def grilles():
    """Affiche le catalogue des grilles d'évaluation."""
    grilles_standard = GrilleEvaluation.query.filter_by(type_grille='standard', active=True).all()
    grilles_perso = []
    if current_user.is_authenticated:
        grilles_perso = GrilleEvaluation.query.filter_by(type_grille='personnalisee', user_id=current_user.id, active=True).all()
    return render_template(
        'cotation/grilles.html',
        grilles_standard=grilles_standard,
        grilles_perso=grilles_perso
    )
# Route détail d'une grille (nécessaire pour le lien dans grilles.html)
@cotation_bp.route('/grille/<int:grille_id>', methods=['GET'], endpoint='grille_detail')
def grille_detail(grille_id):
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    return render_template('cotation/grille_detail.html', grille=grille)


# Route création de grille personnalisée
@cotation_bp.route('/grilles/creer-grille-personalisee', methods=['GET', 'POST'], endpoint='creer_grille_personalisee')
def creer_grille_personalisee():
    """Affiche le formulaire de création de grille personnalisée."""
    # TODO: Remplacer par la vraie logique si besoin
    return render_template('cotation/creer_grille_personalisee.html')

# Route admin pour gestion des grilles, accessible uniquement à l'user 1
@cotation_bp.route('/admin/grilles', methods=['GET', 'POST'], endpoint='admin_grilles')
def admin_grilles():
    if not current_user.is_authenticated or current_user.id != 1:
        flash("Accès réservé à l'administrateur.", "danger")
        return redirect(url_for('cotation.grilles'))

    grilles = GrilleEvaluation.query.order_by(GrilleEvaluation.nom).all()
    domaines = Domaine.query.order_by(Domaine.nom).all()
    indicateurs = Indicateur.query.order_by(Indicateur.nom).all()

    if request.method == 'POST':
        grille_id = request.form.get('grille_id')
        nom = request.form.get('nom')
        description = request.form.get('description')
        type_grille = request.form.get('type_grille')
        reference_scientifique = request.form.get('reference_scientifique')
        domaines_ids = request.form.getlist('domaines[]')
        indicateurs_ids = request.form.getlist('indicateurs[]')

        # Met à jour la grille sélectionnée
        grille = GrilleEvaluation.query.get(grille_id)
        if grille:
            grille.nom = nom or grille.nom
            grille.description = description or grille.description
            grille.type_grille = type_grille or grille.type_grille
            grille.reference_scientifique = reference_scientifique or grille.reference_scientifique
            # Supprime les anciens liens
            from app.models.cotation import GrilleDomaine, DomaineIndicateur, db
            GrilleDomaine.query.filter_by(grille_id=grille.id).delete()
            db.session.commit()
            # Ajoute les nouveaux liens grille-domaine
            for did in domaines_ids:
                # Vérifie si le lien grille-domaine existe déjà
                exists_gd = GrilleDomaine.query.filter_by(grille_id=grille.id, domaine_id=int(did)).first()
                if not exists_gd:
                    gd = GrilleDomaine()
                    gd.grille_id = grille.id
                    gd.domaine_id = int(did)
                    db.session.add(gd)
            db.session.commit()
            # Ajoute les liens domaine-indicateur pour chaque domaine sélectionné
            for did in domaines_ids:
                for iid in indicateurs_ids:
                    # Vérifie que l'indicateur n'est pas déjà lié à un autre domaine
                    already_linked = DomaineIndicateur.query.filter_by(indicateur_id=int(iid)).first()
                    if already_linked:
                        continue
                    exists_di = DomaineIndicateur.query.filter_by(domaine_id=int(did), indicateur_id=int(iid)).first()
                    if not exists_di:
                        di = DomaineIndicateur()
                        di.domaine_id = int(did)
                        di.indicateur_id = int(iid)
                        db.session.add(di)
            db.session.commit()
            flash("Grille et liens mis à jour avec succès.", "success")
        else:
            flash("Grille non trouvée.", "danger")
        return redirect(url_for('cotation.admin_grilles'))

    return render_template('cotation/admin_grilles.html', grilles=grilles, domaines=domaines, indicateurs=indicateurs)

cotation_bp.register_blueprint(seances_bp)
cotation_bp.register_blueprint(analytics_bp)
