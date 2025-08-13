"""Service d'analytics et reporting pour la cotation thérapeutique."""
from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app.models import db, Patient, Seance
from app.models.cotation import GrilleEvaluation, CotationSeance

class AnalyticsService:
    """Service pour l'analyse et le reporting des données de cotation."""

    @staticmethod
    def statistiques_globales(musicotherapeute_id: int) -> Dict[str, Any]:
        """Statistiques globales pour un musicothérapeute."""
        # Compter patients actifs
        nb_patients = Patient.query.filter_by(
            musicotherapeute_id=musicotherapeute_id,
            actif=True
        ).count()

        # Compter séances ce mois
        debut_mois = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        nb_seances_mois = db.session.query(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois
        ).count()

        # Compter cotations totales
        nb_cotations = db.session.query(CotationSeance).join(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id
        ).count()

        # Compter grilles personnalisées
        nb_grilles = GrilleEvaluation.query.filter_by(
            musicotherapeute_id=musicotherapeute_id,
            active=True
        ).count()

        # Score moyen global (30 derniers jours)
        il_y_a_30j = datetime.now() - timedelta(days=30)
        score_moyen = db.session.query(func.avg(CotationSeance.pourcentage_reussite)).join(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= il_y_a_30j
        ).scalar() or 0

        return {
            'nb_patients': nb_patients,
            'nb_seances_mois': nb_seances_mois,
            'nb_cotations': nb_cotations,
            'nb_grilles': nb_grilles,
            'score_moyen_30j': round(score_moyen, 1)
        }

    @staticmethod
    def evolution_patient_detaillee(patient_id: int, grille_id: int, limite: int = 20) -> Dict[str, Any]:
        """Évolution détaillée d'un patient pour une grille donnée."""
        patient = Patient.query.get(patient_id)
        grille = GrilleEvaluation.query.get(grille_id)
        
        if not patient or not grille:
            return {'erreur': 'Patient ou grille introuvable'}

        # Récupérer les cotations
        cotations = db.session.query(CotationSeance, Seance).join(
            Seance, CotationSeance.seance_id == Seance.id
        ).filter(
            Seance.patient_id == patient_id,
            CotationSeance.grille_id == grille_id
        ).order_by(Seance.date_seance.asc()).limit(limite).all()

        if not cotations:
            return {
                'patient': f"{patient.prenom} {patient.nom}",
                'grille': grille.nom,
                'cotations': [],
                'tendance': None,
                'progression': 0
            }

        # Transformer les données
        donnees = []
        for cotation, seance in cotations:
            donnees.append({
                'date': seance.date_seance.isoformat(),
                'score_global': cotation.score_global,
                'score_max': cotation.score_max_possible,
                'pourcentage': round(cotation.pourcentage_reussite, 1),
                'observations': cotation.observations_cotation,
                'seance_id': seance.id
            })

        # Calculer la tendance (régression linéaire simple)
        tendance = None
        progression = 0
        if len(donnees) >= 2:
            premier_score = donnees[0]['pourcentage']
            dernier_score = donnees[-1]['pourcentage']
            progression = dernier_score - premier_score
            
            if progression > 5:
                tendance = 'amelioration'
            elif progression < -5:
                tendance = 'deterioration'
            else:
                tendance = 'stable'

        return {
            'patient': f"{patient.prenom} {patient.nom}",
            'grille': grille.nom,
            'cotations': donnees,
            'tendance': tendance,
            'progression': round(progression, 1)
        }

    @staticmethod
    def patients_a_risque(musicotherapeute_id: int, seuil_score: float = 40.0) -> List[Dict[str, Any]]:
        """Identifie les patients avec scores en baisse ou faibles."""
        # Patients avec score moyen < seuil sur les 3 dernières cotations
        il_y_a_30j = datetime.now() - timedelta(days=30)
        
        subquery = db.session.query(
            CotationSeance.seance_id,
            func.row_number().over(
                partition_by=func.coalesce(Seance.patient_id, 0),
                order_by=desc(Seance.date_seance)
            ).label('rn')
        ).join(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= il_y_a_30j
        ).subquery()

        # Récupérer patients avec moyenne < seuil sur 3 dernières cotations
        resultats = db.session.query(
            Patient.id,
            Patient.prenom,
            Patient.nom,
            func.avg(CotationSeance.pourcentage_reussite).label('score_moyen'),
            func.count(CotationSeance.id).label('nb_cotations')
        ).join(Seance).join(CotationSeance).join(
            subquery, CotationSeance.seance_id == subquery.c.seance_id
        ).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            subquery.c.rn <= 3
        ).group_by(Patient.id, Patient.prenom, Patient.nom).having(
            func.avg(CotationSeance.pourcentage_reussite) < seuil_score
        ).all()

        patients_risque = []
        for patient_id, prenom, nom, score_moyen, nb_cotations in resultats:
            patients_risque.append({
                'patient_id': patient_id,
                'nom_complet': f"{prenom} {nom}",
                'score_moyen': round(score_moyen, 1),
                'nb_cotations': nb_cotations,
                'niveau_risque': 'élevé' if score_moyen < 30 else 'modéré'
            })

        return patients_risque

    @staticmethod
    def rapport_activite_mensuel(musicotherapeute_id: int, annee: int, mois: int) -> Dict[str, Any]:
        """Rapport d'activité détaillé pour un mois donné."""
        debut_mois = datetime(annee, mois, 1)
        if mois == 12:
            fin_mois = datetime(annee + 1, 1, 1)
        else:
            fin_mois = datetime(annee, mois + 1, 1)

        # Séances du mois
        seances = db.session.query(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois,
            Seance.date_seance < fin_mois
        ).all()

        # Cotations du mois
        cotations = db.session.query(CotationSeance).join(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois,
            Seance.date_seance < fin_mois
        ).all()

        # Statistiques par grille
        stats_grilles = db.session.query(
            GrilleEvaluation.nom,
            func.count(CotationSeance.id).label('nb_utilisations'),
            func.avg(CotationSeance.pourcentage_reussite).label('score_moyen')
        ).join(CotationSeance).join(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois,
            Seance.date_seance < fin_mois
        ).group_by(GrilleEvaluation.id, GrilleEvaluation.nom).all()

        # Patients les plus actifs
        patients_actifs = db.session.query(
            Patient.prenom,
            Patient.nom,
            func.count(Seance.id).label('nb_seances')
        ).join(Seance).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois,
            Seance.date_seance < fin_mois
        ).group_by(Patient.id, Patient.prenom, Patient.nom).order_by(
            desc('nb_seances')
        ).limit(10).all()

        return {
            'periode': f"{mois:02d}/{annee}",
            'nb_seances': len(seances),
            'nb_cotations': len(cotations),
            'nb_patients_vus': len(set(s.patient_id for s in seances)),
            'score_moyen_global': round(sum(c.pourcentage_reussite for c in cotations) / len(cotations), 1) if cotations else 0,
            'grilles_utilisees': [
                {
                    'nom': nom,
                    'nb_utilisations': nb_util,
                    'score_moyen': round(score_moy, 1)
                }
                for nom, nb_util, score_moy in stats_grilles
            ],
            'patients_actifs': [
                {
                    'nom': f"{prenom} {nom}",
                    'nb_seances': nb_seances
                }
                for prenom, nom, nb_seances in patients_actifs
            ]
        }
