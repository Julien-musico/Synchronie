"""
API REST pour l'application Synchronie
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from dateutil import parser as date_parser  # type: ignore

from app.services.patient_service import PatientService
from app.services.report_service import ReportService

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

@api.route('/patients/<int:patient_id>/rapport', methods=['POST'])
def generate_patient_report(patient_id: int):
    """Génère un rapport d'évolution de patient sur une période.

    JSON attendu: {"date_debut": "2025-01-01", "date_fin": "2025-02-01", "periodicite": "mensuel|annuel|personnalise"}
    """
    try:
        payload = request.get_json() or {}
        date_debut_raw = payload.get('date_debut')
        date_fin_raw = payload.get('date_fin')
        periodicite = payload.get('periodicite') or None

        if not (date_debut_raw and date_fin_raw):
            return jsonify({'success': False, 'message': 'date_debut et date_fin requis'}), 400

        try:
            # Utiliser dateutil pour souplesse (date seule ou datetime)
            date_debut = date_parser.parse(date_debut_raw)
            date_fin = date_parser.parse(date_fin_raw)
        except Exception:
            return jsonify({'success': False, 'message': 'Format de date invalide'}), 400

        success, message, rapport = ReportService.generate_report(patient_id, date_debut, date_fin, periodicite)
        status = 200 if success else (404 if 'non trouvé' in message.lower() else 400)
        payload_resp = {
            'success': success,
            'message': message,
            'rapport': rapport,
            'date_generation': datetime.now(timezone.utc).isoformat(),
            'date_debut': date_debut.date().isoformat(),
            'date_fin': date_fin.date().isoformat(),
            'periodicite': periodicite
        }
        return jsonify(payload_resp), status
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur serveur: {e}'}), 500
