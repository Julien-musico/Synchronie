from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.patient import Patient
from app.models.session import Session
from app.models.rapport import Rapport
from app import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Page d'accueil"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord principal"""
    # Statistiques rapides pour le thérapeute connecté
    stats = {
        'patients_actifs': Patient.query.filter_by(
            therapist_id=current_user.id,
            status='active'
        ).count(),
        'sessions_semaine': Session.query.join(Patient).filter(
            Patient.therapist_id == current_user.id,
            Session.date >= db.func.date('now', '-7 days')
        ).count(),
        'rapports_en_attente': Rapport.query.join(Patient).filter(
            Patient.therapist_id == current_user.id,
            Rapport.status.in_(['draft', 'generated'])
        ).count()
    }
    
    # Dernières séances
    recent_sessions = Session.query.join(Patient).filter(
        Patient.therapist_id == current_user.id
    ).order_by(Session.date.desc()).limit(5).all()
    
    # Patients nécessitant un rapport
    patients_due_reports = []
    for patient in Patient.query.filter_by(therapist_id=current_user.id, status='active').all():
        if patient.is_due_for_report():
            patients_due_reports.append(patient)
    
    return render_template('dashboard.html', 
                         stats=stats,
                         recent_sessions=recent_sessions,
                         patients_due_reports=patients_due_reports)

@bp.route('/about')
def about():
    """Page à propos de Synchronie"""
    return render_template('about.html')

@bp.route('/help')
@login_required
def help():
    """Page d'aide et documentation"""
    return render_template('help.html')

@bp.route('/profile')
@login_required
def profile():
    """Profil utilisateur"""
    return render_template('profile.html', user=current_user)

@bp.route('/settings')
@login_required
def settings():
    """Paramètres de l'application"""
    return render_template('settings.html')

@bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
