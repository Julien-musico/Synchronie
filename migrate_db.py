from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()
app.app_context().push()

print('Migration: Renommage de la colonne activites_musicales en activites_realisees')

try:
    # Pour SQLite, on utilise PRAGMA table_info
    result = db.session.execute(text("PRAGMA table_info(seances)"))
    columns = [row[1] for row in result]  # row[1] contient le nom de la colonne
    print(f'Colonnes trouvées: {columns}')
    
    if 'activites_musicales' in columns and 'activites_realisees' not in columns:
        print('Renommage de activites_musicales en activites_realisees...')
        db.session.execute(text('ALTER TABLE seances RENAME COLUMN activites_musicales TO activites_realisees'))
        db.session.commit()
        print('✅ Migration réussie')
    elif 'activites_realisees' in columns:
        print('✅ La colonne activites_realisees existe déjà')
    else:
        print('❌ Structure inattendue')
        print(f'Colonnes disponibles: {columns}')
        
except Exception as e:
    print(f'❌ Erreur: {e}')
    db.session.rollback()
