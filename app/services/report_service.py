"""Service de génération de rapports d'évolution patient via Mistral AI"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any

from app.models import Patient, Seance
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
    def generate_report(patient_id: int, date_debut: datetime, date_fin: datetime, periodicite: str | None = None) -> tuple[bool, str, str | None]:
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
            "Tu es un musicothérapeute expérimenté rédigeant un rapport d'évolution clinique synthétique et structuré."\
            "\nContraintes:"\
            "\n- Français professionnel, concis, factuel"\
            "\n- Aucune invention: uniquement les synthèses et données fournies"\
            "\n- Si une donnée manque, indiquer 'non documenté' sans extrapoler"\
            "\n- Pas de listes à puces dans l'introduction mais sections courtes autorisées (2-4)"\
            "\nStructure impérative:"\
            "\n1. Contexte & Période"\
            "\n2. Synthèse de l'évolution clinique (comportements, réponses musicales, aspects émotionnels / relationnels)"\
            "\n3. Progression par rapport aux objectifs thérapeutiques"\
            "\n4. Analyse des tendances d'engagement (si données)"\
            "\n5. Points de vigilance & recommandations"\
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
        except Exception as e:
            logger.error(f'Echec génération rapport Mistral: {e}')
            return False, f'Erreur génération IA: {e}', None

        return True, 'Rapport généré', rapport
