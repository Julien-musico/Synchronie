"""
Module de correction automatique de la base de données
Intégré dans l'application pour correction à la volée
"""
import logging

from sqlalchemy import text

from app.models import db

logger = logging.getLogger(__name__)

def auto_fix_database():
    """
    Correction automatique de la structure de base de données
    À appeler si une erreur de colonne manquante est détectée
    """
    try:
        logger.info("🔧 Auto-correction de la base de données en cours...")

        engine_name = db.engine.name
        logger.info(f"📊 Type de base de données: {engine_name}")

        if engine_name == 'postgresql':
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'seances'
                  AND column_name IN ('activites_musicales', 'activites_realisees')
            """))
        else:
            result = db.session.execute(text("PRAGMA table_info(seances)"))
            columns_info = result.fetchall()
            relevant_columns = [row[1] for row in columns_info if row[1] in ['activites_musicales', 'activites_realisees']]
            result = [(col,) for col in relevant_columns]

        columns = [row[0] for row in result]
        logger.info(f"📋 Colonnes activites trouvées: {columns}")

        if 'activites_musicales' in columns and 'activites_realisees' not in columns:
            logger.info("🔄 Renommage activites_musicales → activites_realisees...")
            db.session.execute(text('ALTER TABLE seances RENAME COLUMN activites_musicales TO activites_realisees'))
            db.session.commit()
            logger.info("✅ Migration de colonne réussie!")
            return True

        if 'activites_realisees' not in columns:
            logger.info("➕ Ajout de la colonne activites_realisees...")
            db.session.execute(text('ALTER TABLE seances ADD COLUMN activites_realisees TEXT'))
            db.session.commit()
            logger.info("✅ Colonne ajoutée avec succès!")
            return True

        logger.info("✅ La colonne activites_realisees existe déjà")
        return True
    except Exception as e:  # pragma: no cover
        logger.error(f"❌ Erreur lors de l'auto-correction: {e}")
        import contextlib
        with contextlib.suppress(Exception):
            db.session.rollback()
        return False

def safe_query_seances(*args, **kwargs):
    """
    Wrapper sécurisé pour les requêtes sur la table seances
    Tente une auto-correction si la colonne activites_realisees manque
    """
    try:
        # Tentative de requête normale
        from app.models import Seance
        return Seance.query.filter(*args, **kwargs)
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'activites_realisees' in error_msg and 'does not exist' in error_msg:
            logger.warning("🚨 Colonne activites_realisees manquante détectée, tentative de correction...")
            if auto_fix_database():
                logger.info("✅ Auto-correction réussie, nouvelle tentative de requête...")
                from app.models import Seance
                return Seance.query.filter(*args, **kwargs)
            logger.error("❌ Auto-correction échouée")
            raise
        # Autre erreur, on la relance
        raise
