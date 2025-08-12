from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.patient import Patient, PatientStatus, Gender
from app.models.session import Session
from app import db
from datetime import datetime

bp = Blueprint('patients', __name__)

@bp.route('/')
@login_required
def list_patients():
    """Liste des patients du thérapeute"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', 'active', type=str)
    
    query = Patient.query.filter_by(therapist_id=current_user.id)
    
    # Filtrage par statut
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Recherche par nom
    if search:
        query = query.filter(
            db.or_(
                Patient.first_name.contains(search),
                Patient.last_name.contains(search)
            )
        )
    
    patients = query.order_by(Patient.last_name, Patient.first_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('patients/list.html', 
                         patients=patients, 
                         search=search,
                         status_filter=status_filter)

@bp.route('/new', methods=['GET', 'POST'])
@login_required  
def new_patient():
    """Création d'un nouveau patient"""
    if request.method == 'POST':
        try:
            patient = Patient(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                gender=Gender(request.form.get('gender')),
                therapist_id=current_user.id,
                start_date=datetime.now().date()
            )
            
            # Informations optionnelles
            patient.address = request.form.get('address', '')
            patient.phone = request.form.get('phone', '')
            patient.email = request.form.get('email', '')
            patient.medical_history = request.form.get('medical_history', '')
            patient.therapeutic_objectives = request.form.get('therapeutic_objectives', '')
            patient.initial_assessment = request.form.get('initial_assessment', '')
            
            db.session.add(patient)
            db.session.commit()
            
            flash(f'Patient {patient.get_full_name()} créé avec succès !', 'success')
            return redirect(url_for('patients.view_patient', id=patient.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du patient : {str(e)}', 'error')
    
    return render_template('patients/new.html')

@bp.route('/<int:id>')
@login_required
def view_patient(id):
    """Affichage du dossier complet d'un patient"""
    patient = Patient.query.get_or_404(id)
    
    # Vérification des droits d'accès
    if not current_user.can_access_patient(patient):
        flash('Vous n\'avez pas accès à ce dossier patient.', 'error')
        return redirect(url_for('patients.list_patients'))
    
    # Statistiques du patient
    stats = {
        'total_sessions': patient.get_total_sessions(),
        'last_session': patient.get_last_session_date(),
        'age': patient.get_age(),
        'duration_months': (datetime.now().date() - patient.start_date).days // 30
    }
    
    # Dernières séances
    recent_sessions = patient.sessions.order_by(Session.date.desc()).limit(10).all()
    
    # Rapports récents
    recent_reports = patient.rapports.order_by(db.desc('created_at')).limit(5).all()
    
    return render_template('patients/view.html', 
                         patient=patient,
                         stats=stats,
                         recent_sessions=recent_sessions,
                         recent_reports=recent_reports)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    """Modification d'un patient"""
    patient = Patient.query.get_or_404(id)
    
    if not current_user.can_access_patient(patient):
        flash('Vous n\'avez pas accès à ce dossier patient.', 'error')
        return redirect(url_for('patients.list_patients'))
    
    if request.method == 'POST':
        try:
            patient.first_name = request.form.get('first_name')
            patient.last_name = request.form.get('last_name')
            patient.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            patient.gender = Gender(request.form.get('gender'))
            patient.address = request.form.get('address', '')
            patient.phone = request.form.get('phone', '')
            patient.email = request.form.get('email', '')
            patient.medical_history = request.form.get('medical_history', '')
            patient.therapeutic_objectives = request.form.get('therapeutic_objectives', '')
            patient.status = PatientStatus(request.form.get('status'))
            
            if request.form.get('end_date'):
                patient.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
            
            db.session.commit()
            flash('Dossier patient mis à jour avec succès !', 'success')
            return redirect(url_for('patients.view_patient', id=patient.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour : {str(e)}', 'error')
    
    return render_template('patients/edit.html', patient=patient)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    """Suppression d'un patient (soft delete)"""
    patient = Patient.query.get_or_404(id)
    
    if not current_user.can_access_patient(patient):
        flash('Vous n\'avez pas accès à ce dossier patient.', 'error')
        return redirect(url_for('patients.list_patients'))
    
    try:
        # Soft delete - marquer comme discontinué plutôt que supprimer
        patient.status = PatientStatus.DISCONTINUED
        patient.end_date = datetime.now().date()
        db.session.commit()
        
        flash(f'Dossier de {patient.get_full_name()} marqué comme discontinué.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'error')
    
    return redirect(url_for('patients.list_patients'))

@bp.route('/search-api')
@login_required
def search_patients_api():
    """API de recherche de patients pour autocomplétion"""
    query = request.args.get('q', '', type=str)
    
    if len(query) < 2:
        return jsonify([])
    
    patients = Patient.query.filter(
        Patient.therapist_id == current_user.id,
        db.or_(
            Patient.first_name.contains(query),
            Patient.last_name.contains(query)
        )
    ).limit(10).all()
    
    results = []
    for patient in patients:
        results.append({
            'id': patient.id,
            'name': patient.get_full_name(),
            'age': patient.get_age(),
            'status': patient.status.value
        })
    
    return jsonify(results)
