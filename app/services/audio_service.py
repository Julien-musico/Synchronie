import openai
import whisper
from typing import Optional, Dict, Any
import os
import tempfile
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)

class AudioTranscriptionService:
    """Service de transcription audio utilisant OpenAI Whisper"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        
        # Modèle Whisper local pour la transcription
        self.whisper_model = None
        self._load_whisper_model()
    
    def _load_whisper_model(self):
        """Charge le modèle Whisper local"""
        try:
            # Utilise le modèle "base" par défaut (bon compromis qualité/vitesse)
            self.whisper_model = whisper.load_model("base")
            logger.info("Modèle Whisper chargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle Whisper : {e}")
    
    def transcribe_audio_file(self, file_path: str, language: str = "fr") -> Dict[str, Any]:
        """
        Transcrit un fichier audio en texte
        
        Args:
            file_path: Chemin vers le fichier audio
            language: Langue du contenu audio (fr par défaut)
            
        Returns:
            Dict contenant la transcription et les métadonnées
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Fichier audio non trouvé : {file_path}")
            
            # Préprocessing audio si nécessaire
            processed_file = self._preprocess_audio(file_path)
            
            # Transcription avec Whisper
            if self.whisper_model:
                result = self.whisper_model.transcribe(
                    processed_file,
                    language=language,
                    task="transcribe",
                    temperature=0.0  # Plus déterministe
                )
                
                # Nettoyage du fichier temporaire
                if processed_file != file_path:
                    os.remove(processed_file)
                
                return {
                    "text": result["text"].strip(),
                    "segments": result.get("segments", []),
                    "language": result.get("language", language),
                    "duration": self._get_audio_duration(file_path),
                    "success": True,
                    "error": None
                }
            else:
                # Fallback vers l'API OpenAI si le modèle local n'est pas disponible
                return self._transcribe_with_api(processed_file, language)
                
        except Exception as e:
            logger.error(f"Erreur lors de la transcription : {e}")
            return {
                "text": "",
                "segments": [],
                "language": language,
                "duration": 0,
                "success": False,
                "error": str(e)
            }
    
    def _transcribe_with_api(self, file_path: str, language: str) -> Dict[str, Any]:
        """Transcription via l'API OpenAI (fallback)"""
        try:
            with open(file_path, "rb") as audio_file:
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )
            
            return {
                "text": response.get("text", "").strip(),
                "segments": response.get("segments", []),
                "language": response.get("language", language),
                "duration": response.get("duration", 0),
                "success": True,
                "error": None
            }
        except Exception as e:
            logger.error(f"Erreur API OpenAI : {e}")
            return {
                "text": "",
                "segments": [],
                "language": language,
                "duration": 0,
                "success": False,
                "error": str(e)
            }
    
    def _preprocess_audio(self, file_path: str) -> str:
        """
        Préprocesse le fichier audio pour optimiser la transcription
        """
        try:
            # Charger l'audio
            audio = AudioSegment.from_file(file_path)
            
            # Vérifier si des modifications sont nécessaires
            needs_processing = False
            
            # Normaliser le volume si trop faible
            if audio.dBFS < -25:
                audio = audio.normalize()
                needs_processing = True
            
            # Convertir en mono si stéréo
            if audio.channels > 1:
                audio = audio.set_channels(1)
                needs_processing = True
            
            # Ajuster la fréquence d'échantillonnage si nécessaire
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
                needs_processing = True
            
            # Si aucun traitement nécessaire, retourner le fichier original
            if not needs_processing:
                return file_path
            
            # Sauvegarder le fichier traité
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                audio.export(tmp_file.name, format="wav")
                return tmp_file.name
                
        except Exception as e:
            logger.warning(f"Erreur lors du préprocessing audio : {e}")
            # En cas d'erreur, retourner le fichier original
            return file_path
    
    def _get_audio_duration(self, file_path: str) -> float:
        """Obtient la durée du fichier audio en secondes"""
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # Convertir ms en secondes
        except Exception as e:
            logger.warning(f"Impossible de déterminer la durée audio : {e}")
            return 0.0
    
    def extract_timestamps(self, segments: list) -> list:
        """
        Extrait les timestamps des segments pour identifier les moments clés
        """
        timestamps = []
        for segment in segments:
            timestamps.append({
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", "").strip(),
                "confidence": segment.get("confidence", 0)
            })
        return timestamps
    
    def detect_speaker_changes(self, segments: list, threshold: float = 2.0) -> list:
        """
        Détecte les changements de locuteur basés sur les pauses
        """
        speaker_segments = []
        current_speaker = 1
        
        for i, segment in enumerate(segments):
            if i > 0:
                # Si pause > threshold secondes, nouveau locuteur probable
                prev_end = segments[i-1].get("end", 0)
                current_start = segment.get("start", 0)
                
                if current_start - prev_end > threshold:
                    current_speaker += 1
            
            speaker_segments.append({
                **segment,
                "speaker": current_speaker
            })
        
        return speaker_segments
