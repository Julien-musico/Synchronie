"""
Routes pour la gestion des patients (interface web)
"""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.patient_service import PatientService

patients = Blueprint('patients', __name__)

@patients.route('/')
def list_patients():
    """Liste des patients"""
    patients_list = PatientService.get_all_patients()
    return render_template('patients/list.html', patients=patients_list)

@patients.route('/nouveau')
def new_patient():
    """Formulaire de création d'un nouveau patient"""
    return render_template('patients/form_simple.html', patient=None)

@patients.route('/create', methods=['POST'])
def create_patient():
    """Traitement de la création d'un patient"""
    print("DEBUG: Route create_patient appelée")
    print(f"DEBUG: Méthode: {request.method}")
    print(f"DEBUG: Form data: {request.form}")
    
    data = request.form.to_dict()
    print(f"DEBUG: Data dict: {data}")
    
    success, message, patient = PatientService.create_patient(data)
    print(f"DEBUG: Résultat création: success={success}, message='{message}', patient={patient}")
    
    if success:
        flash(message, 'success')
        print(f"DEBUG: Redirection vers patient {patient.id}")
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
    flash(message, 'error')
    print("DEBUG: Retour au formulaire avec erreur")
    return render_template('patients/form_simple.html', patient=None)

@patients.route('/debug-form')
def debug_form():
    """Formulaire de test simple pour diagnostiquer"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Création Patient</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h2>Test Création Patient</h2>
            <form method="POST" action="/patients/create">
                <div class="mb-3">
                    <label for="nom" class="form-label">Nom *</label>
                    <input type="text" class="form-control" id="nom" name="nom" required>
                </div>
                <div class="mb-3">
                    <label for="prenom" class="form-label">Prénom *</label>
                    <input type="text" class="form-control" id="prenom" name="prenom" required>
                </div>
                <div class="mb-3">
                    <label for="email" class="form-label">Email</label>
                    <input type="email" class="form-control" id="email" name="email">
                </div>
                <button type="submit" class="btn btn-primary">Créer Patient</button>
            </form>
        </div>
    </body>
    </html>
    '''

@patients.route('/test-create')
def test_create():
    """Route de test pour diagnostiquer la création"""
    # Création d'un patient de test
    test_data = {
        'nom': 'Test',
        'prenom': 'Patient',
        'telephone': '0123456789',
        'email': 'test@example.com'
    }
    
    success, message, patient = PatientService.create_patient(test_data)
    
    if success:
        return f"✅ Patient créé avec succès ! ID: {patient.id}, Nom: {patient.prenom} {patient.nom}"
    return f"❌ Erreur lors de la création: {message}"

@patients.route('/<int:patient_id>')
def view_patient(patient_id):
    """Affichage d'un patient"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    # Rendre la fonction datetime disponible dans le template
    return render_template('patients/detail.html', patient=patient, now=datetime.now)

@patients.route('/<int:patient_id>/modifier')
def edit_patient(patient_id):
    """Formulaire de modification d'un patient"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    return render_template('patients/form_simple.html', patient=patient)

@patients.route('/<int:patient_id>/update', methods=['POST'])
def update_patient(patient_id):
    """Traitement de la modification d'un patient"""
    data = request.form.to_dict()
    success, message, patient = PatientService.update_patient(patient_id, data)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))
    flash(message, 'error')
    return redirect(url_for('patients.edit_patient', patient_id=patient_id))
