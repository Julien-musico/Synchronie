"""
Routes principales de l'application
"""
from flask import Blueprint, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required  # type: ignore
from sqlalchemy import text

from app.models import db
from app.services.patient_service import PatientService
from app.services.seance_service import SeanceService

main = Blueprint('main', __name__)

@main.route('/api/health')
def health_check():
    """Endpoint de santé pour Render"""
    return jsonify({'status': 'healthy', 'service': 'synchronie'}), 200

@main.route('/api/health/db')
def health_db():  # type: ignore[no-untyped-def]
    """Vérifie schéma minimal DB: colonnes essentielles présentes."""
    issues: list[str] = []
    details: dict[str, dict] = {}
    tables = {
        'grille_evaluation': {'required': {'id','nom','type_grille','domaines_config','active','publique','date_creation','date_modification'}},
        'patients': {'required': {'id','nom','prenom','actif','date_creation','date_modification'}},
        'seances': {'required': {'id','patient_id','date_seance','date_creation','date_modification'}}
    }
    try:
        for table, meta in tables.items():
            result = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns WHERE table_name=:t
            """), {'t': table})
            cols = {r[0] for r in result}
            required = meta['required']
            missing = required - cols
            if missing:
                issues.append(f"{table}: colonnes manquantes {sorted(missing)}")
            # Compter lignes (résilient si table vide)
            try:
                count = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()  # type: ignore
            except Exception as ce:  # pragma: no cover
                count = None
                issues.append(f"{table}: count échec ({ce})")
            details[table] = {
                'missing': sorted(missing),
                'count': count
            }
        # Vérification cohérence: domaines_config non NULL
        try:
            bad = db.session.execute(text("SELECT COUNT(*) FROM grille_evaluation WHERE domaines_config IS NULL"))
            bad_count = bad.scalar()  # type: ignore
            if bad_count:
                issues.append(f"grille_evaluation: {bad_count} lignes domaines_config NULL")
                details['grille_evaluation']['bad_domaines_config_null'] = bad_count
        except Exception:
            pass
        status = 'ok'
        http_code = 200
        if issues:
            status = 'degraded'
            http_code = 206
        return jsonify({'status': status, 'issues': issues, 'details': details}), http_code
    except Exception as e:  # pragma: no cover
        return jsonify({'status': 'error', 'error': str(e)}), 500

@main.route('/')
def index():
    """Redirige vers login si non authentifié, sinon dashboard."""
    if not current_user.is_authenticated:  # type: ignore
        return redirect(url_for('auth.login'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required  # type: ignore
def dashboard():
    """Tableau de bord principal"""
    try:
        # Récupérer les statistiques pour le dashboard
        patients = PatientService.get_all_patients()
        patients_actifs = [p for p in patients if p.actif]
        
        # Statistiques des séances
        seances_stats = SeanceService.get_seances_statistics()
        
        stats = {
            'total_patients': len(patients),
            'patients_actifs': len(patients_actifs),
            'total_seances': seances_stats['total_seances'],
            'seances_ce_mois': seances_stats['seances_ce_mois'],
            'duree_moyenne': seances_stats['duree_moyenne'],
            'engagement_moyen': seances_stats['engagement_moyen']
        }
        
        # Séances récentes (toujours calculées si d'autres vues en ont besoin)
        seances_recentes = SeanceService.get_recent_seances(5)

        # Actions rapides (liens robustes vers les sections clés)
        quick_actions = {
            'nouveau_patient': {'url': url_for('patients.new_patient')},
            # Nouvelle séance requiert un patient, on redirige vers la liste des patients
            'nouvelle_seance': {'url': url_for('patients.list_patients')},
            # Nouveau rapport: renvoi vers la liste des patients par défaut (sélection du contexte)
            'nouveau_rapport': {'url': url_for('patients.list_patients')},
            'agenda': {'url': url_for('seances.list_seances')},
        }

        # Patients récents (6 max) — si modèle expose date_modification, on pourrait trier, sinon on tronque
        recent_patients = patients[:6]
        recent_patients_url = url_for('patients.list_patients')

        return render_template(
            'dashboard.html',
            stats=stats,
            seances_recentes=seances_recentes,
            quick_actions=quick_actions,
            recent_patients=recent_patients,
            recent_patients_url=recent_patients_url,
        )
    except Exception as e:
        # Log l'erreur pour debugging
        print(f"Erreur dashboard: {e}")
        # Retourner un dashboard minimal en cas d'erreur
        stats = {
            'total_patients': 0,
            'patients_actifs': 0,
            'total_seances': 0,
            'seances_ce_mois': 0,
            'duree_moyenne': 0,
            'engagement_moyen': 0
        }
        quick_actions = {
            'nouveau_patient': {'url': url_for('patients.new_patient')},
            'nouvelle_seance': {'url': url_for('patients.list_patients')},
            'nouveau_rapport': {'url': url_for('patients.list_patients')},
            'agenda': {'url': url_for('seances.list_seances')},
        }
        return render_template(
            'dashboard.html',
            stats=stats,
            seances_recentes=[],
            quick_actions=quick_actions,
            recent_patients=[],
            recent_patients_url=url_for('patients.list_patients'),
        )
