"""
API REST pour l'application Synchronie
"""
from flask import Blueprint, jsonify, request

from app.services.patient_service import PatientService

api = Blueprint('api', __name__)

@api.route('/health')
def health_check():
    """Point de contrôle pour vérifier que l'application fonctionne"""
    return jsonify({
        'status': 'healthy',
        'message': 'Synchronie API is running',
        'version': '1.0.0'
    })

@api.route('/patients', methods=['GET'])
def get_patients():
    """Récupère la liste des patients"""
    try:
        patients = PatientService.get_all_patients()
        return jsonify({
            'success': True,
            'data': [patient.to_dict() for patient in patients],
            'count': len(patients)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération des patients: {str(e)}'
        }), 500

@api.route('/patients', methods=['POST'])
def create_patient():
    """Crée un nouveau patient"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Données JSON requises'
            }), 400
        
        success, message, patient = PatientService.create_patient(data)
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': patient.to_dict()
            }), 201
        return jsonify({
            'success': False,
            'message': message
        }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la création du patient: {str(e)}'
        }), 500

@api.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Récupère un patient par son ID"""
    try:
        patient = PatientService.get_patient_by_id(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'message': 'Patient non trouvé'
            }), 404
        
        return jsonify({
            'success': True,
            'data': patient.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération du patient: {str(e)}'
        }), 500

@api.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Met à jour un patient"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Données JSON requises'
            }), 400
        
        success, message, patient = PatientService.update_patient(patient_id, data)
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': patient.to_dict()
            })
        return jsonify({
            'success': False,
            'message': message
        }), 400 if 'non trouvé' not in message else 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la mise à jour du patient: {str(e)}'
        }), 500

@api.route('/patients/search', methods=['GET'])
def search_patients():
    """Recherche des patients"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'message': 'Paramètre de recherche requis'
            }), 400
        
        patients = PatientService.search_patients(query)
        return jsonify({
            'success': True,
            'data': [patient.to_dict() for patient in patients],
            'count': len(patients)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la recherche: {str(e)}'
        }), 500
