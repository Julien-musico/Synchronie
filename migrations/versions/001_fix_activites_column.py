"""Correction colonne activites_realisees

Revision ID: 001_fix_activites_column
Revises: 
Create Date: 2025-08-13 12:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_fix_activites_column'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Renommer activites_musicales en activites_realisees si elle existe"""
    # Vérifier si la colonne activites_musicales existe et la renommer
    connection = op.get_bind()
    
    # Pour PostgreSQL, vérifier l'existence de la colonne
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'seances' 
        AND column_name IN ('activites_musicales', 'activites_realisees')
    """))
    
    existing_columns = [row[0] for row in result]
    
    if 'activites_musicales' in existing_columns and 'activites_realisees' not in existing_columns:
        # Renommer la colonne
        op.alter_column('seances', 'activites_musicales', 
                       new_column_name='activites_realisees')
    elif 'activites_realisees' not in existing_columns and 'activites_musicales' not in existing_columns:
        # Créer la colonne si elle n'existe pas du tout
        op.add_column('seances', sa.Column('activites_realisees', sa.Text(), nullable=True))


def downgrade():
    """Renommer activites_realisees en activites_musicales"""
    connection = op.get_bind()
    
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'seances' 
        AND column_name = 'activites_realisees'
    """))
    
    if result.fetchone():
        op.alter_column('seances', 'activites_realisees', 
                       new_column_name='activites_musicales')
