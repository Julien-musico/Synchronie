"""Migration pour ajouter les tables de cotation thérapeutique

Revision ID: add_cotation_tables
Revises: 
Create Date: 2025-08-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_cotation_tables'
# Chaînage correct: cette migration dépend maintenant de la correction de colonne
down_revision = '001_fix_activites_column'
depends_on = None


def upgrade():
    # Créer la table grille_evaluation
    op.create_table('grille_evaluation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('type_grille', sa.String(length=50), nullable=False),
    sa.Column('reference_scientifique', sa.String(length=100), nullable=True),
    sa.Column('domaines_config', sa.Text(), nullable=False),
    sa.Column('musicotherapeute_id', sa.Integer(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('publique', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['musicotherapeute_id'], ['musicotherapeute.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_grille_evaluation_active'), 'grille_evaluation', ['active'], unique=False)
    op.create_index(op.f('ix_grille_evaluation_musicotherapeute_id'), 'grille_evaluation', ['musicotherapeute_id'], unique=False)
    op.create_index(op.f('ix_grille_evaluation_publique'), 'grille_evaluation', ['publique'], unique=False)

    # Créer la table cotation_seance
    op.create_table('cotation_seance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('seance_id', sa.Integer(), nullable=False),
    sa.Column('grille_id', sa.Integer(), nullable=False),
    sa.Column('scores_detailles', sa.Text(), nullable=False),
    sa.Column('score_global', sa.Float(), nullable=True),
    sa.Column('score_max_possible', sa.Float(), nullable=True),
    sa.Column('pourcentage_reussite', sa.Float(), nullable=True),
    sa.Column('observations_cotation', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['grille_id'], ['grille_evaluation.id'], ),
    sa.ForeignKeyConstraint(['seance_id'], ['seance.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('seance_id', 'grille_id', name='unique_cotation_seance_grille')
    )
    op.create_index(op.f('ix_cotation_seance_grille_id'), 'cotation_seance', ['grille_id'], unique=False)
    op.create_index(op.f('ix_cotation_seance_seance_id'), 'cotation_seance', ['seance_id'], unique=False)

    # Créer la table objectif_therapeutique
    op.create_table('objectif_therapeutique',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('grille_id', sa.Integer(), nullable=False),
    sa.Column('domaine_cible', sa.String(length=100), nullable=False),
    sa.Column('objectif_description', sa.Text(), nullable=False),
    sa.Column('criteres_reussite', sa.Text(), nullable=True),
    sa.Column('echeance_prevue', sa.Date(), nullable=True),
    sa.Column('statut', sa.String(length=20), nullable=True),
    sa.Column('notes_progression', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['grille_id'], ['grille_evaluation.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_objectif_therapeutique_grille_id'), 'objectif_therapeutique', ['grille_id'], unique=False)
    op.create_index(op.f('ix_objectif_therapeutique_patient_id'), 'objectif_therapeutique', ['patient_id'], unique=False)
    op.create_index(op.f('ix_objectif_therapeutique_statut'), 'objectif_therapeutique', ['statut'], unique=False)


def downgrade():
    # Supprimer les tables dans l'ordre inverse
    op.drop_index(op.f('ix_objectif_therapeutique_statut'), table_name='objectif_therapeutique')
    op.drop_index(op.f('ix_objectif_therapeutique_patient_id'), table_name='objectif_therapeutique')
    op.drop_index(op.f('ix_objectif_therapeutique_grille_id'), table_name='objectif_therapeutique')
    op.drop_table('objectif_therapeutique')
    
    op.drop_index(op.f('ix_cotation_seance_seance_id'), table_name='cotation_seance')
    op.drop_index(op.f('ix_cotation_seance_grille_id'), table_name='cotation_seance')
    op.drop_table('cotation_seance')
    
    op.drop_index(op.f('ix_grille_evaluation_publique'), table_name='grille_evaluation')
    op.drop_index(op.f('ix_grille_evaluation_musicotherapeute_id'), table_name='grille_evaluation')
    op.drop_index(op.f('ix_grille_evaluation_active'), table_name='grille_evaluation')
    op.drop_table('grille_evaluation')
