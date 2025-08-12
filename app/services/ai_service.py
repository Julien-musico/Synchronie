from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from typing import Dict, List, Any, Optional
import json
import logging
import re

logger = logging.getLogger(__name__)

class TherapeuticAnalysisService:
    """Service d'analyse thérapeutique utilisant Mistral AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('MISTRAL_API_KEY')
        if self.api_key:
            self.client = MistralClient(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("Clé API Mistral non configurée")
    
    def analyze_session_transcription(self, transcription: str, patient_context: Dict = None) -> Dict[str, Any]:
        """
        Analyse une transcription de séance et génère une synthèse thérapeutique
        
        Args:
            transcription: Texte transcrit de la séance
            patient_context: Contexte du patient (pathologies, objectifs, etc.)
            
        Returns:
            Dict contenant l'analyse thérapeutique structurée
        """
        if not self.client:
            return self._get_error_response("Service d'analyse IA non disponible")
        
        try:
            # Construction du prompt spécialisé en musicothérapie
            prompt = self._build_analysis_prompt(transcription, patient_context)
            
            # Appel à l'API Mistral
            response = self.client.chat(
                model="mistral-large-latest",
                messages=[
                    ChatMessage(role="system", content=self._get_system_prompt()),
                    ChatMessage(role="user", content=prompt)
                ],
                temperature=0.3,  # Plus déterministe pour l'analyse thérapeutique
                max_tokens=2000
            )
            
            # Extraction et structuration de la réponse
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_response(analysis_text)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse IA : {e}")
            return self._get_error_response(str(e))
    
    def _get_system_prompt(self) -> str:
        """Prompt système pour contextualiser l'IA comme expert en musicothérapie"""
        return """Tu es un expert en musicothérapie avec plus de 15 ans d'expérience clinique. 
        Tu analyses les transcriptions de séances pour aider les musicothérapeutes dans leur documentation.
        
        Tes compétences incluent :
        - Analyse des interactions thérapeutiques musicales
        - Identification des progrès et difficultés des patients
        - Reconnaissance des techniques de musicothérapie utilisées
        - Évaluation de l'engagement et de la participation
        - Respect des standards déontologiques et du secret médical
        
        Tu dois produire des analyses objectives, professionnelles et utiles pour le suivi thérapeutique.
        Utilise un langage médical approprié tout en restant accessible.
        Respecte toujours la confidentialité et évite les interprétations non fondées."""
    
    def _build_analysis_prompt(self, transcription: str, patient_context: Dict = None) -> str:
        """Construit le prompt d'analyse personnalisé"""
        
        context_section = ""
        if patient_context:
            context_section = f"""
CONTEXTE PATIENT :
- Pathologies : {patient_context.get('pathologies', 'Non spécifiées')}
- Objectifs thérapeutiques : {patient_context.get('objectives', 'Non spécifiés')}
- Âge : {patient_context.get('age', 'Non spécifié')}
- Historique musical : {patient_context.get('music_background', 'Non spécifié')}
"""
        
        prompt = f"""
{context_section}

TRANSCRIPTION DE SÉANCE :
{transcription}

ANALYSE DEMANDÉE :
Analyse cette séance de musicothérapie et fournis une synthèse structurée selon le format suivant :

## SYNTHÈSE THÉRAPEUTIQUE

### Déroulement de la séance
[Description objective du déroulement]

### Engagement et participation
[Évaluation de l'engagement du patient]

### Techniques utilisées
[Techniques de musicothérapie identifiées]

### Observations cliniques
[Observations comportementales, émotionnelles, cognitives]

### Progrès observés
[Progrès identifiés par rapport aux objectifs]

### Difficultés rencontrées
[Difficultés ou résistances observées]

### Moments significatifs
[3-5 moments clés de la séance avec timestamps approximatifs]

### Recommandations
[Suggestions pour les prochaines séances]

### Score d'engagement global
[Score de 1 à 5 avec justification]

Sois précis, objectif et base-toi uniquement sur les éléments observables dans la transcription.
"""
        return prompt
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, Any]:
        """Parse et structure la réponse de l'IA"""
        try:
            # Extraction des sections principales
            sections = {}
            
            # Patterns pour extraire les sections
            patterns = {
                'deroulement': r'### Déroulement de la séance\s*\n(.*?)(?=###|$)',
                'engagement': r'### Engagement et participation\s*\n(.*?)(?=###|$)',
                'techniques': r'### Techniques utilisées\s*\n(.*?)(?=###|$)',
                'observations': r'### Observations cliniques\s*\n(.*?)(?=###|$)',
                'progres': r'### Progrès observés\s*\n(.*?)(?=###|$)',
                'difficultes': r'### Difficultés rencontrées\s*\n(.*?)(?=###|$)',
                'moments_cles': r'### Moments significatifs\s*\n(.*?)(?=###|$)',
                'recommandations': r'### Recommandations\s*\n(.*?)(?=###|$)',
                'score_engagement': r'### Score d\'engagement global\s*\n(.*?)(?=###|$)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                sections[key] = match.group(1).strip() if match else ""
            
            # Extraction des moments clés structurés
            key_moments = self._extract_key_moments(sections.get('moments_cles', ''))
            
            # Extraction du score
            engagement_score = self._extract_engagement_score(sections.get('score_engagement', ''))
            
            return {
                'success': True,
                'error': None,
                'summary': {
                    'deroulement': sections.get('deroulement', ''),
                    'engagement': sections.get('engagement', ''),
                    'techniques': sections.get('techniques', ''),
                    'observations': sections.get('observations', ''),
                    'progres': sections.get('progres', ''),
                    'difficultes': sections.get('difficultes', ''),
                    'recommandations': sections.get('recommandations', '')
                },
                'key_moments': key_moments,
                'engagement_score': engagement_score,
                'raw_analysis': analysis_text
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing de l'analyse : {e}")
            return {
                'success': False,
                'error': f"Erreur de parsing : {str(e)}",
                'summary': {},
                'key_moments': [],
                'engagement_score': None,
                'raw_analysis': analysis_text
            }
    
    def _extract_key_moments(self, moments_text: str) -> List[Dict]:
        """Extrait et structure les moments clés"""
        moments = []
        lines = moments_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.') or line.startswith('5.')):
                # Nettoyer la ligne
                clean_line = re.sub(r'^[-*\d.]\s*', '', line)
                
                # Extraire le timestamp si présent
                timestamp_match = re.search(r'(\d{1,2}:\d{2}|\d{1,2}min|\d{1,2}h\d{2})', clean_line)
                timestamp = timestamp_match.group(1) if timestamp_match else None
                
                # Nettoyer le texte du timestamp
                if timestamp:
                    description = clean_line.replace(timestamp, '').strip(' :-')
                else:
                    description = clean_line
                
                moments.append({
                    'timestamp': timestamp,
                    'description': description,
                    'importance': 'high'  # Par défaut, tous les moments extraits sont importants
                })
        
        return moments[:5]  # Limiter à 5 moments maximum
    
    def _extract_engagement_score(self, score_text: str) -> Dict:
        """Extrait le score d'engagement"""
        try:
            # Recherche d'un score numérique
            score_match = re.search(r'(\d)[/\s]*5', score_text)
            if score_match:
                score = int(score_match.group(1))
                return {
                    'score': score,
                    'max_score': 5,
                    'justification': score_text
                }
        except:
            pass
        
        return {
            'score': None,
            'max_score': 5,
            'justification': score_text
        }
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Retourne une réponse d'erreur structurée"""
        return {
            'success': False,
            'error': error_message,
            'summary': {},
            'key_moments': [],
            'engagement_score': None,
            'raw_analysis': ''
        }
    
    def generate_report_content(self, sessions_data: List[Dict], patient_context: Dict = None) -> Dict[str, Any]:
        """
        Génère le contenu d'un rapport périodique basé sur plusieurs séances
        """
        if not self.client:
            return self._get_error_response("Service d'analyse IA non disponible")
        
        try:
            # Construction du prompt pour rapport périodique
            prompt = self._build_report_prompt(sessions_data, patient_context)
            
            response = self.client.chat(
                model="mistral-large-latest",
                messages=[
                    ChatMessage(role="system", content=self._get_report_system_prompt()),
                    ChatMessage(role="user", content=prompt)
                ],
                temperature=0.2,
                max_tokens=3000
            )
            
            report_text = response.choices[0].message.content
            return self._parse_report_response(report_text)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport : {e}")
            return self._get_error_response(str(e))
    
    def _get_report_system_prompt(self) -> str:
        """Prompt système spécialisé pour la génération de rapports"""
        return """Tu es un musicothérapeute expert rédigeant des rapports périodiques d'évolution.
        
        Tes rapports doivent être :
        - Professionnels et conformes aux standards médicaux
        - Objectifs et basés sur les observations cliniques
        - Structurés et facilement compréhensibles par les équipes médicales
        - Respectueux du secret médical et de la déontologie
        
        Tu analyses l'évolution du patient sur une période donnée et fournis des recommandations
        pour la suite du parcours thérapeutique."""
    
    def _build_report_prompt(self, sessions_data: List[Dict], patient_context: Dict = None) -> str:
        """Construit le prompt pour la génération de rapport"""
        
        context_section = ""
        if patient_context:
            context_section = f"""
INFORMATIONS PATIENT :
- Âge : {patient_context.get('age', 'Non spécifié')}
- Pathologies : {patient_context.get('pathologies', 'Non spécifiées')}
- Objectifs initiaux : {patient_context.get('objectives', 'Non spécifiés')}
- Début du suivi : {patient_context.get('start_date', 'Non spécifié')}
"""
        
        sessions_section = "SYNTHÈSES DES SÉANCES :\n\n"
        for i, session in enumerate(sessions_data, 1):
            sessions_section += f"Séance {i} ({session.get('date', 'Date inconnue')}) :\n"
            sessions_section += f"- Synthèse : {session.get('summary', 'Non disponible')}\n"
            sessions_section += f"- Score engagement : {session.get('engagement_score', 'N/A')}/5\n"
            sessions_section += f"- Moments clés : {', '.join([m.get('description', '') for m in session.get('key_moments', [])])}\n\n"
        
        prompt = f"""
{context_section}

{sessions_section}

GÉNÉRATION DE RAPPORT PÉRIODIQUE :

Analyse cette période de suivi et génère un rapport structuré selon le format suivant :

## RAPPORT D'ÉVOLUTION - MUSICOTHÉRAPIE

### Synthèse exécutive
[Résumé en 3-4 phrases de l'évolution globale]

### Analyse de la période
[Analyse détaillée des {len(sessions_data)} séances]

### Évolution par domaines
[Progression dans les différents domaines thérapeutiques]

### Objectifs atteints
[Bilan par rapport aux objectifs initiaux]

### Difficultés persistantes
[Challenges identifiés nécessitant attention]

### Recommandations thérapeutiques
[Orientations pour la suite du suivi]

### Objectifs pour la période suivante
[Nouveaux objectifs à poursuivre]

### Conclusion
[Bilan global et perspectives]

Base-toi uniquement sur les données fournies et reste objectif dans tes analyses.
"""
        return prompt
    
    def _parse_report_response(self, report_text: str) -> Dict[str, Any]:
        """Parse la réponse de génération de rapport"""
        try:
            sections = {}
            
            patterns = {
                'synthese_executive': r'### Synthèse exécutive\s*\n(.*?)(?=###|$)',
                'analyse_periode': r'### Analyse de la période\s*\n(.*?)(?=###|$)',
                'evolution_domaines': r'### Évolution par domaines\s*\n(.*?)(?=###|$)',
                'objectifs_atteints': r'### Objectifs atteints\s*\n(.*?)(?=###|$)',
                'difficultes': r'### Difficultés persistantes\s*\n(.*?)(?=###|$)',
                'recommandations': r'### Recommandations thérapeutiques\s*\n(.*?)(?=###|$)',
                'objectifs_futurs': r'### Objectifs pour la période suivante\s*\n(.*?)(?=###|$)',
                'conclusion': r'### Conclusion\s*\n(.*?)(?=###|$)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, report_text, re.DOTALL | re.IGNORECASE)
                sections[key] = match.group(1).strip() if match else ""
            
            return {
                'success': True,
                'error': None,
                'report_sections': sections,
                'raw_report': report_text
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing du rapport : {e}")
            return {
                'success': False,
                'error': f"Erreur de parsing : {str(e)}",
                'report_sections': {},
                'raw_report': report_text
            }
