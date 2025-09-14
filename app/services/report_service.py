"""Service de génération de rapports d'évolution patient via Mistral AI"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any

from app.models import Patient, Seance, RapportPatient, db
from app.services.audio_service import AudioTranscriptionService

logger = logging.getLogger(__name__)

class ReportService:
    """Génère un rapport d'évolution global sur une période de séances.

    Le rapport s'appuie sur :
    - Les synthèses IA existantes (synthese_ia)
    - Les scores d'engagement si disponibles
    - Les objectifs / observations
    """

    @staticmethod
    def _format_date(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).strftime('%d/%m/%Y')

    @staticmethod
    def collect_seances(patient_id: int, date_debut: datetime, date_fin: datetime) -> list[Seance]:
        q = (Seance.query
             .filter(Seance.patient_id == patient_id,
                     Seance.date_seance >= date_debut,
                     Seance.date_seance <= date_fin)
             .order_by(Seance.date_seance.asc()))
        return q.all()  # type: ignore

    @staticmethod
    def build_context(seances: list[Seance]) -> dict[str, Any]:
        syntheses = []
        engagements: list[int] = []
        for s in seances:
            if s.synthese_ia:
                syntheses.append({
                    'date': s.date_seance,
                    'texte': s.synthese_ia.strip()
                })
            if s.score_engagement is not None:
                engagements.append(int(s.score_engagement))
        return {
            'syntheses': syntheses,
            'engagements': engagements,
        }

    @staticmethod
    def generate_report(patient_id: int, date_debut: datetime, date_fin: datetime, periodicite: str | None = None) -> tuple[bool, str, dict | None]:
        patient = Patient.query.get(patient_id)
        if not patient:
            return False, 'Patient non trouvé', None

        if date_debut > date_fin:
            return False, 'Période invalide (date début > date fin)', None

        seances = ReportService.collect_seances(patient_id, date_debut, date_fin)
        if not seances:
            return False, 'Aucune séance sur la période sélectionnée', None

        context = ReportService.build_context(seances)
        syntheses = context['syntheses']
        engagements = context['engagements']

        # Statistiques simples
        nb_seances = len(seances)
        engagement_moyen = round(sum(engagements) / len(engagements), 1) if engagements else 'NA'
        engagement_tendance = ''
        if len(engagements) >= 2:
            if engagements[-1] > engagements[0]:
                engagement_tendance = 'en amélioration'
            elif engagements[-1] < engagements[0]:
                engagement_tendance = 'en diminution'
            else:
                engagement_tendance = 'stable'

        periode_label = f"du {ReportService._format_date(date_debut)} au {ReportService._format_date(date_fin)}"
        if periodicite == 'mensuel':
            periode_label += ' (rapport mensuel)'
        elif periodicite == 'annuel':
            periode_label += ' (rapport annuel)'

        # Construire l'entrée consolidée pour LLM
        syntheses_concat = '\n\n'.join([
            f"[Synthèse {i+1} - {r['date'].strftime('%d/%m/%Y')}]: {r['texte']}" for i, r in enumerate(syntheses)
        ])

        system_prompt = (
            "Tu es musicothérapeute clinicien. Produis un rapport d'évolution sobre et professionnel."\
            "\nContraintes stylistiques strictes:"\
            "\n- Ton clinique neutre, formulation directe, phrases complètes"\
            "\n- Aucune puce, aucun astérisque, aucun tiret de liste, aucun guillemet décoratif"\
            "\n- Pas de numérotation explicite (pas de 1., 2., etc.)"\
            "\n- Pas de mise en forme artificielle, pas d'emoji"\
            "\n- Regrouper en paragraphes courts distincts (3 à 6 lignes) : Contexte/Période ; Evolution clinique ; Progression objectifs ; Engagement ; Points de vigilance & recommandations"\
            "\n- Un espace simple entre les phrases, pas de double saut de ligne sauf pour séparer les sections"\
            "\nRègles de contenu:"\
            "\n- Uniquement les informations dérivables des synthèses fournies"\
            "\n- Si une dimension est absente: écrire 'non documenté' sans extrapoler"\
            "\n- Synthétiser sans répéter textuellement toutes les synthèses, extraire les tendances"\
            "\nSortie finale: suite de paragraphes sobres, sans balisage ni titre explicite, séparés par UNE ligne vide."\
        )

        user_prompt = f"""Données Patient:\n- Prénom: {patient.prenom}\n- Pathologie: {patient.pathologie or 'Non renseignée'}\n- Objectifs thérapeutiques: {patient.objectifs_therapeutiques or 'Non renseignés'}\n\nPériode analysée: {periode_label}\nNombre de séances: {nb_seances}\nEngagement moyen: {engagement_moyen}\nTendance engagement: {engagement_tendance or 'non déterminable'}\n\nSynthèses disponibles:\n{syntheses_concat or 'Aucune synthèse'}\n\nProduit un rapport d'évolution structuré conformément aux instructions."""

        # Réutiliser le client Mistral du service audio pour homogénéité
        try:
            audio_service = AudioTranscriptionService()
        except Exception as e:
            return False, f'Client IA indisponible: {e}', None
        if not audio_service.mistral_client:
            return False, 'Mistral non configuré: impossible de générer un rapport', None

        try:
            rapport = audio_service._mistral_call(system_prompt, user_prompt)  # type: ignore
            if rapport:
                # Normalisation légère: retirer puces éventuelles accidentelles
                lines = []
                for raw in rapport.splitlines():
                    stripped = raw.strip()
                    if stripped.startswith(('- ', '* ', '• ')):
                        stripped = stripped[2:].lstrip()
                    # retirer guillemets droits simples décoratifs entourant une ligne entière
                    if (stripped.startswith(('"', "'")) and stripped.endswith(('"', "'")) and len(stripped) > 2):
                        stripped = stripped[1:-1].strip()
                    lines.append(stripped)
                rapport = '\n'.join(lines).strip()
            if not rapport or not rapport.strip():
                logger.warning("Rapport IA vide ou non généré - vérifier prompts ou réponse API")
        except Exception as e:
            logger.error(f'Echec génération rapport Mistral: {e}')
            return False, f'Erreur génération IA: {e}', None

        # Sauvegarde du rapport
        try:
            rapport_obj = RapportPatient()  # type: ignore
            rapport_obj.patient_id = patient_id  # type: ignore
            rapport_obj.date_debut = date_debut.date()  # type: ignore
            rapport_obj.date_fin = date_fin.date()  # type: ignore
            rapport_obj.periodicite = periodicite  # type: ignore
            rapport_obj.contenu = rapport or ''  # type: ignore
            rapport_obj.modele = getattr(audio_service, 'mistral_model', None)  # type: ignore
            rapport_obj.fournisseur = 'mistral'  # type: ignore
            db.session.add(rapport_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Échec sauvegarde rapport: {e}")
            return False, f'Rapport généré mais non sauvegardé: {e}', {'rapport': rapport}

        return True, 'Rapport généré', {
            'rapport': rapport,
            'id': rapport_obj.id,
            'date_generation': rapport_obj.date_creation.isoformat(),
            'date_debut': rapport_obj.date_debut.isoformat(),
            'date_fin': rapport_obj.date_fin.isoformat(),
            'periodicite': rapport_obj.periodicite,
            'modele': rapport_obj.modele,
            'fournisseur': rapport_obj.fournisseur
        }
