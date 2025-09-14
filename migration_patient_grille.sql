-- Migration structure patient_grille / patients
-- Applique: FK grille_id, contrainte d'unicité, conversion date_assignation, rename index
-- Sûr en ré-exécution (tests d'existence).

BEGIN;

-- 1. FK sur grille_id
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name='patient_grille' AND constraint_type='FOREIGN KEY'
              AND constraint_name='patient_grille_grille_id_fkey'
    ) THEN
        ALTER TABLE patient_grille
            ADD CONSTRAINT patient_grille_grille_id_fkey
            FOREIGN KEY (grille_id) REFERENCES grille_evaluation(id)
            ON DELETE CASCADE;
    END IF;
END$$;

-- 2. Contrainte d'unicité patient/grille
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name='patient_grille'
          AND constraint_type='UNIQUE'
          AND constraint_name='_patient_grille_uc'
    ) THEN
        ALTER TABLE patient_grille
            ADD CONSTRAINT _patient_grille_uc UNIQUE (patient_id, grille_id);
    END IF;
END$$;

-- 3. Conversion date_assignation (date -> timestamp)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
         WHERE table_name='patient_grille'
           AND column_name='date_assignation'
           AND data_type='date'
    ) THEN
        ALTER TABLE patient_grille
            ALTER COLUMN date_assignation TYPE timestamp
            USING (CASE WHEN date_assignation IS NOT NULL THEN date_assignation::timestamp ELSE NULL END);
    END IF;
END$$;

-- 4. Renommage index ancien (optionnel)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename='patients'
          AND indexname='idx_patients_musicotherapeute'
    ) THEN
        ALTER INDEX idx_patients_musicotherapeute RENAME TO idx_patients_user_id;
    END IF;
END$$;

COMMIT;

-- Fin migration