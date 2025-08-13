"""Service d'analytics et reporting pour la cotation thérapeutique."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func

from app.models import Patient, Seance, db
from app.models.cotation import CotationSeance, GrilleEvaluation


class AnalyticsService:
    """Service pour l'analyse et le reporting des données de cotation."""

    @staticmethod
    def statistiques_globales(musicotherapeute_id: int) -> dict[str, Any]:
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
    def evolution_patient_detaillee(patient_id: int, grille_id: int, limite: int = 20) -> dict[str, Any]:
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
    def patients_a_risque(musicotherapeute_id: int, seuil_score: float = 40.0) -> list[dict[str, Any]]:
        """Identifie les patients avec scores en baisse ou faibles."""
        # Approche simplifiée pour éviter les problèmes de jointure
        il_y_a_30j = datetime.now() - timedelta(days=30)
        
        # Récupérer tous les patients du thérapeute
        patients = Patient.query.filter_by(musicotherapeute_id=musicotherapeute_id).all()
        patients_risque = []
        
        for patient in patients:
            # Récupérer les dernières cotations du patient
            cotations_recentes = db.session.query(CotationSeance).join(Seance).filter(
                Seance.patient_id == patient.id,
                CotationSeance.date_creation >= il_y_a_30j
            ).order_by(CotationSeance.date_creation.desc()).limit(3).all()
            
            if cotations_recentes:
                scores = [c.pourcentage_reussite for c in cotations_recentes if c.pourcentage_reussite is not None]
                if scores:
                    score_moyen = sum(scores) / len(scores)
                    if score_moyen < seuil_score:
                        patients_risque.append({
                            'patient_id': patient.id,
                            'nom': patient.nom,
                            'prenom': patient.prenom,
                            'score_moyen': round(score_moyen, 1),
                            'nb_cotations': len(scores),
                            'niveau_risque': 'élevé' if score_moyen < 30 else 'modéré',
                            'derniere_cotation': {
                                'score_total': cotations_recentes[0].pourcentage_reussite,
                                'date': cotations_recentes[0].date_creation.strftime('%d/%m/%Y')
                            }
                        })

        return patients_risque

    @staticmethod
    def rapport_activite_mensuel(musicotherapeute_id: int, annee: int, mois: int) -> dict[str, Any]:
        """Rapport d'activité détaillé pour un mois donné."""
        debut_mois = datetime(annee, mois, 1)
        fin_mois = datetime(annee + 1, 1, 1) if mois == 12 else datetime(annee, mois + 1, 1)

        seances = db.session.query(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois,
            Seance.date_seance < fin_mois
        ).all()

        cotations = db.session.query(CotationSeance).join(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois,
            Seance.date_seance < fin_mois
        ).all()

        stats_grilles = db.session.query(
            GrilleEvaluation.nom,
            func.count(CotationSeance.id).label('nb_utilisations'),
            func.avg(CotationSeance.pourcentage_reussite).label('score_moyen')
        ).join(CotationSeance).join(Seance).join(Patient).filter(
            Patient.musicotherapeute_id == musicotherapeute_id,
            Seance.date_seance >= debut_mois,
            Seance.date_seance < fin_mois
        ).group_by(GrilleEvaluation.id, GrilleEvaluation.nom).all()

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
            'nb_patients_vus': len({s.patient_id for s in seances}),
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
