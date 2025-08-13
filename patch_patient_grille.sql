-- Patch SQL pour créer la table PatientGrille
-- À exécuter sur la base de données PostgreSQL de production
-- Date: 2025-08-13

-- Création de la table patient_grille pour l'association patients-grilles
CREATE TABLE IF NOT EXISTS patient_grille (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    grille_id INTEGER NOT NULL,
    priorite INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    assignee_par INTEGER,
    date_assignation TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date_fin TIMESTAMP WITH TIME ZONE,
    commentaires TEXT,
    date_creation TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    date_modification TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Contraintes de clés étrangères
    CONSTRAINT fk_patient_grille_patient 
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    CONSTRAINT fk_patient_grille_grille 
        FOREIGN KEY (grille_id) REFERENCES grille_evaluation(id) ON DELETE CASCADE,
    
    -- Contrainte d'unicité pour éviter les doublons
    CONSTRAINT unique_patient_grille 
        UNIQUE (patient_id, grille_id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_patient_grille_patient_id ON patient_grille(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_grille_grille_id ON patient_grille(grille_id);
CREATE INDEX IF NOT EXISTS idx_patient_grille_active ON patient_grille(active);
CREATE INDEX IF NOT EXISTS idx_patient_grille_priorite ON patient_grille(patient_id, priorite);

-- Trigger pour mettre à jour automatiquement date_modification
CREATE OR REPLACE FUNCTION update_patient_grille_modified_time()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_modification = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patient_grille_modtime 
    BEFORE UPDATE ON patient_grille 
    FOR EACH ROW 
    EXECUTE FUNCTION update_patient_grille_modified_time();

-- Vérification que les tables référencées existent
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'patients') THEN
        RAISE EXCEPTION 'Table patients n''existe pas. Veuillez d''abord créer la table patients.';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'grille_evaluation') THEN
        RAISE EXCEPTION 'Table grille_evaluation n''existe pas. Veuillez d''abord créer la table grille_evaluation.';
    END IF;
END $$;

-- Message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Table patient_grille créée avec succès avec tous les index et triggers.';
END $$;
