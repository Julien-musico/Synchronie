"""
Service de transcription audio et analyse IA pour Synchronie
Utilise OpenAI Whisper pour la transcription et GPT pour l'analyse
"""
import logging
import os
import tempfile
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI
from werkzeug.datastructures import FileStorage

try:  # Third-party optional
    from mistralai import Mistral  # type: ignore
except ImportError:  # pragma: no cover
    Mistral = None  # type: ignore

from app.models import Seance, db

logger = logging.getLogger(__name__)

class AudioTranscriptionService:
    """Service pour la transcription d'enregistrements audio de séances"""
    
    # Formats audio supportés
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'webm'}
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB (limite OpenAI Whisper)
    
    def __init__(self):
        """Initialise le service (OpenAI pour transcription Whisper, Mistral pour synthèse si disponible)"""
        self.openai_client: Optional[OpenAI] = None
        self.mistral_client = None  # type: ignore

        openai_key = os.environ.get('OPENAI_API_KEY')
        mistral_key = os.environ.get('MISTRAL_API_KEY')
        mistral_model = os.environ.get('MISTRAL_MODEL', 'mistral-large-latest')

        # Initialisation Mistral (synthèse)
        if mistral_key:
            if Mistral is not None:
                try:
                    self.mistral_client = Mistral(api_key=mistral_key)
                    self.mistral_model = mistral_model
                    logger.info(f"✅ Client Mistral initialisé (modèle: {mistral_model})")
                except Exception as e:
                    logger.error(f"❌ Impossible d'initialiser Mistral: {e}")
            else:
                logger.warning("⚠️ Paquet 'mistralai' non installé: pip install mistralai pour activer Mistral")

        # Initialisation OpenAI (nécessaire pour Whisper). On garde logique minimale.
        if openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
            except Exception as e:
                logger.error(f"❌ Échec initialisation OpenAI: {e}")
        else:
            logger.warning("OPENAI_API_KEY non configurée: transcription Whisper désactivée")

        if not self.openai_client and not self.mistral_client:
            raise ValueError("Aucun client IA initialisé (ni OpenAI pour Whisper ni Mistral pour synthèse)")
    
    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Vérifie si le fichier a une extension autorisée"""
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in AudioTranscriptionService.ALLOWED_EXTENSIONS)
    
    @staticmethod
    def validate_audio_file(file: FileStorage) -> Tuple[bool, str]:
        """
        Valide un fichier audio uploadé
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "Aucun fichier sélectionné"
        
        if not AudioTranscriptionService.is_allowed_file(file.filename):
            return False, f"Format non supporté. Formats autorisés: {', '.join(AudioTranscriptionService.ALLOWED_EXTENSIONS)}"
        
        # Vérifier la taille (si possible)
        if (
            hasattr(file, 'content_length')
            and file.content_length
            and file.content_length > AudioTranscriptionService.MAX_FILE_SIZE
        ):
            return False, "Fichier trop volumineux. Taille maximum: 25 MB"
        
        return True, ""
    
    def transcribe_audio(self, audio_file: FileStorage) -> Tuple[bool, str, Optional[str]]:
        """
        Transcrit un fichier audio en texte
        
        Args:
            audio_file: Fichier audio à transcrire
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, transcription)
        """
        # Vérifier que le client OpenAI (Whisper) est initialisé
        if self.openai_client is None:
            logger.error("Client OpenAI non initialisé pour la transcription")
            return False, "Service de transcription non disponible (Whisper indisponible)", None
            
        try:
            # Validation du fichier
            is_valid, error_msg = self.validate_audio_file(audio_file)
            if not is_valid:
                return False, error_msg, None
            
            logger.info(f"Début de la transcription pour: {audio_file.filename}")
            
            # Créer un fichier temporaire pour l'upload vers OpenAI
            filename = audio_file.filename or 'audio.mp3'
            with tempfile.NamedTemporaryFile(
                suffix=f".{filename.rsplit('.', 1)[1].lower()}", 
                delete=False
            ) as temp_file:
                
                # Sauvegarder le fichier temporairement
                audio_file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Transcription avec Whisper - version simplifiée
                with open(temp_file_path, 'rb') as audio_data:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_data,
                        language="fr",  # Français
                        response_format="text"
                    )
                
                transcription_text = str(transcript) if transcript else ""
                logger.info(f"Transcription réussie: {len(transcription_text)} caractères")
                
                return True, "Transcription réussie", transcription_text
                
            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
        
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            return False, f"Erreur de transcription: {str(e)}", None
    
    def generate_session_analysis(self, transcription: str, patient_info: Dict[str, Any], session_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Génère une analyse IA de la séance à partir de la transcription
        
        Args:
            transcription: Texte transcrit de la séance
            patient_info: Informations sur le patient
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, analysis)
        """
        # Vérifier que le client Mistral est disponible
        if not self.mistral_client:
            logger.error("Client Mistral non initialisé pour la synthèse")
            return False, "Synthèse indisponible (Mistral non configuré)", None
            
        try:
            logger.info("Génération de l'analyse IA de la séance")
            
            # Prompt spécialisé pour l'analyse de musicothérapie avec format imposé
            system_prompt = (
                "Tu es musicothérapeute spécialisé en psychologie. Tu produis une synthèse clinique concise et rigoureuse."\
                "\nContraintes strictes:"\
                "\n- Style professionnel, sobre, factuel, en français clair"\
                "\n- Première personne (\"je\")"\
                "\n- Aucune invention: uniquement les éléments fournis"\
                "\n- Pas de listes, pas de puces, pas de sous-titres"\
                "\n- Un seul paragraphe continu"\
                "\n- Pas de double espaces, pas de verbosité"\
                "\nFormat de sortie OBLIGATOIRE:"\
                "\nSéance de Musicothérapie : [paragraphe unique de 5 à 8 phrases couvrant: contexte pertinent, comportements ou réponses musicales observés, réactions émotionnelles/motrices notables, qualité de l'interaction, progression par rapport aux objectifs mentionnés, points de vigilance et éventuelle orientation/recommandation succincte]"\
                "\nN'inclus pas la structure entre crochets dans la réponse finale, remplace-la directement par le texte rédigé."\
            )
            
            contexte = ""
            if session_context:
                objectifs = session_context.get('objectifs_seance') or ''
                activites = session_context.get('activites_realisees') or ''
                observations = session_context.get('observations') or ''
                if any([objectifs, activites, observations]):
                    contexte = ("\n\nContexte de séance fourni par le thérapeute :\n"
                               f"- Objectifs de séance : {objectifs or 'Non renseignés'}\n"
                               f"- Activités réalisées : {activites or 'Non renseignées'}\n"
                               f"- Observations : {observations or 'Non renseignées'}\n")

            user_prompt = f"""Informations du patient :
- Prénom : {patient_info.get('prenom', 'Non renseigné')}
- Pathologie : {patient_info.get('pathologie', 'Non renseignée')}
- Objectifs thérapeutiques : {patient_info.get('objectifs_therapeutiques', 'Non renseignés')}

{contexte}

Contenu à analyser (transcription ou notes) :
{transcription}

Génère une synthèse thérapeutique détaillée de cette séance de musicothérapie."""
            
            try:
                m_response = self.mistral_client.responses.create(
                    model=self.mistral_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000,
                )
                analysis = ""
                try:
                    output_blocks = getattr(m_response, 'output', []) or []  # type: ignore
                    if output_blocks:
                        first_block = output_blocks[0]
                        block_content = getattr(first_block, 'content', [])  # type: ignore
                        if block_content:
                            analysis = getattr(block_content[0], 'text', '')  # type: ignore
                except Exception as parse_err:  # pragma: no cover
                    logger.warning(f"⚠️ Parsing réponse Mistral: {parse_err}")
                if not analysis:
                    analysis = str(m_response)
            except Exception as e:
                logger.error(f"Erreur génération Mistral: {e}")
                return False, f"Erreur d'analyse IA: {str(e)}", None
            logger.info(f"Analyse IA générée: {len(analysis)} caractères")
            
            return True, "Analyse générée avec succès", analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'analyse: {e}")
            return False, f"Erreur d'analyse IA: {str(e)}", None
    
    def process_session_recording(self, audio_file: FileStorage, seance_id: int) -> Tuple[bool, str]:
        """
        Traite complètement un enregistrement de séance
        
        Args:
            audio_file: Fichier audio de la séance
            seance_id: ID de la séance à mettre à jour
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Récupérer la séance
            seance = Seance.query.get(seance_id)
            if not seance:
                return False, "Séance non trouvée"
            
            # Transcription
            success, message, transcription = self.transcribe_audio(audio_file)
            if not success:
                return False, f"Échec de la transcription: {message}"
            
            # Informations du patient pour l'analyse
            patient_info = {
                'prenom': seance.patient.prenom,
                'pathologie': seance.patient.pathologie,
                'objectifs_therapeutiques': seance.patient.objectifs_therapeutiques
            }
            
            # Génération de l'analyse IA
            if transcription:  # Vérifier que transcription n'est pas None
                success, message, analysis = self.generate_session_analysis(transcription, patient_info)
                if not success:
                    logger.warning(f"Analyse IA échouée: {message}")
                    analysis = "Analyse automatique non disponible"
            else:
                analysis = "Transcription non disponible pour l'analyse"
            
            # Mettre à jour la séance avec les résultats
            seance.transcription_audio = transcription
            seance.synthese_ia = analysis
            # Ne pas sauvegarder le fichier audio, juste la transcription
            
            db.session.commit()
            
            logger.info(f"Traitement complet réussi pour la séance {seance_id}")
            return True, "Enregistrement traité avec succès"
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'enregistrement: {e}")
            db.session.rollback()
            return False, f"Erreur de traitement: {str(e)}"
    
    @staticmethod
    def get_audio_info(file: FileStorage) -> Dict[str, Any]:
        """
        Récupère les informations d'un fichier audio
        
        Args:
            file: Fichier audio
            
        Returns:
            Dict contenant les informations du fichier
        """
        info: Dict[str, Any] = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': getattr(file, 'content_length', 0)
        }
        
        try:
            # Vérifier que le nom de fichier existe
            if not file.filename:
                return info
                
            # Utiliser mutagen pour obtenir plus d'infos si possible
            try:
                from mutagen import File as MutagenFile  # type: ignore
            except ImportError:
                logger.warning("Mutagen non installé - informations audio limitées")
                return info
            
            with tempfile.NamedTemporaryFile(
                suffix=f".{file.filename.rsplit('.', 1)[1].lower()}"
            ) as temp_file:
                file.save(temp_file.name)
                file.seek(0)  # Reset pour une utilisation ultérieure
                
                audio_file = MutagenFile(temp_file.name)  # type: ignore
                if audio_file and hasattr(audio_file, 'info'):  # type: ignore
                    info.update({
                        'duration': getattr(audio_file.info, 'length', 0),  # type: ignore
                        'bitrate': getattr(audio_file.info, 'bitrate', 0),  # type: ignore
                        'channels': getattr(audio_file.info, 'channels', 0)  # type: ignore
                    })
        
        except Exception as e:
            logger.warning(f"Impossible de lire les métadonnées audio: {e}")
        
        return info
