-- ================================
-- Synchronie Cotation Schema Patch
-- Idempotent: sûr à relancer
-- Version: 2025-08-13-02 (ajout correctif patients.musicotherapeute_id manquante en prod)
-- ================================

-- 0. Table users (auth) : création si absente
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    nom VARCHAR(120),
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    date_modification TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);


-- 1. Table patients: ajouter colonne musicotherapeute_id si absente
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='patients' AND column_name='musicotherapeute_id'
    ) THEN
        ALTER TABLE patients ADD COLUMN musicotherapeute_id INTEGER;
        BEGIN
            ALTER TABLE patients
                ADD CONSTRAINT patients_musicotherapeute_fk
                FOREIGN KEY (musicotherapeute_id) REFERENCES users(id) ON DELETE SET NULL;
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table users introuvable, FK ignorée';
        END;
        CREATE INDEX IF NOT EXISTS idx_patients_musicotherapeute ON patients(musicotherapeute_id);
    END IF;
END $$;

-- 1b. Correction si l'index n'a pas été créé (exécution précédente interrompue)
CREATE INDEX IF NOT EXISTS idx_patients_musicotherapeute ON patients(musicotherapeute_id);

-- 2. Table grille_evaluation
CREATE TABLE IF NOT EXISTS grille_evaluation (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    type_grille VARCHAR(50) NOT NULL,
    reference_scientifique VARCHAR(100),
    domaines_config TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    publique BOOLEAN DEFAULT FALSE,
    musicotherapeute_id INTEGER,
    date_creation TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    date_modification TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Assurer présence colonnes timestamp si table préexistante sans celles-ci
ALTER TABLE grille_evaluation
    ADD COLUMN IF NOT EXISTS date_creation TIMESTAMPTZ DEFAULT NOW() NOT NULL;
ALTER TABLE grille_evaluation
    ADD COLUMN IF NOT EXISTS date_modification TIMESTAMPTZ DEFAULT NOW() NOT NULL;

-- Ajouter colonne musicotherapeute_id si table existait sans
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='grille_evaluation' AND column_name='musicotherapeute_id'
    ) THEN
        ALTER TABLE grille_evaluation ADD COLUMN musicotherapeute_id INTEGER;
    END IF;
END $$;

-- Index + FK (FK conditionnelle)
CREATE INDEX IF NOT EXISTS idx_grille_eval_musicotherapeute ON grille_evaluation(musicotherapeute_id);
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname='grille_eval_musicotherapeute_fk'
    ) THEN
        BEGIN
            ALTER TABLE grille_evaluation
                ADD CONSTRAINT grille_eval_musicotherapeute_fk
                FOREIGN KEY (musicotherapeute_id) REFERENCES users(id) ON DELETE SET NULL;
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table users introuvable, FK ignorée';
        END;
    END IF;
END $$;

-- 3. Table cotation_seance
CREATE TABLE IF NOT EXISTS cotation_seance (
    id SERIAL PRIMARY KEY,
    seance_id INTEGER NOT NULL,
    grille_id INTEGER NOT NULL,
    scores_detailles TEXT NOT NULL,
    score_global DOUBLE PRECISION,
    score_max_possible DOUBLE PRECISION,
    pourcentage_reussite DOUBLE PRECISION,
    observations_cotation TEXT,
    date_creation TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    date_modification TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Assurer présence des colonnes timestamp si table préexistante sans celles-ci
ALTER TABLE cotation_seance
    ADD COLUMN IF NOT EXISTS date_creation TIMESTAMPTZ DEFAULT NOW() NOT NULL;
ALTER TABLE cotation_seance
    ADD COLUMN IF NOT EXISTS date_modification TIMESTAMPTZ DEFAULT NOW() NOT NULL;

-- Index
CREATE INDEX IF NOT EXISTS idx_cotation_seance_seance ON cotation_seance(seance_id);
CREATE INDEX IF NOT EXISTS idx_cotation_seance_grille ON cotation_seance(grille_id);

-- FKs conditionnelles
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='cotation_seance_seance_fk') THEN
        BEGIN
            ALTER TABLE cotation_seance
                ADD CONSTRAINT cotation_seance_seance_fk
                FOREIGN KEY (seance_id) REFERENCES seances(id) ON DELETE CASCADE;
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table seances manquante, FK ignorée';
        END;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='cotation_seance_grille_fk') THEN
        BEGIN
            ALTER TABLE cotation_seance
                ADD CONSTRAINT cotation_seance_grille_fk
                FOREIGN KEY (grille_id) REFERENCES grille_evaluation(id) ON DELETE CASCADE;
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table grille_evaluation manquante, FK ignorée';
        END;
    END IF;
END $$;

-- 4. Table objectif_therapeutique
CREATE TABLE IF NOT EXISTS objectif_therapeutique (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    grille_id INTEGER NOT NULL,
    domaine_cible VARCHAR(100) NOT NULL,
    indicateur_cible VARCHAR(100) NOT NULL,
    score_initial DOUBLE PRECISION,
    score_cible DOUBLE PRECISION NOT NULL,
    echeance DATE,
    atteint BOOLEAN DEFAULT FALSE,
    actif BOOLEAN DEFAULT TRUE,
    description TEXT,
    date_creation TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    date_modification TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

ALTER TABLE objectif_therapeutique
    ADD COLUMN IF NOT EXISTS date_creation TIMESTAMPTZ DEFAULT NOW() NOT NULL;
ALTER TABLE objectif_therapeutique
    ADD COLUMN IF NOT EXISTS date_modification TIMESTAMPTZ DEFAULT NOW() NOT NULL;

CREATE INDEX IF NOT EXISTS idx_obj_ther_patient ON objectif_therapeutique(patient_id);
CREATE INDEX IF NOT EXISTS idx_obj_ther_grille ON objectif_therapeutique(grille_id);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='objectif_ther_patient_fk') THEN
        BEGIN
            ALTER TABLE objectif_therapeutique
                ADD CONSTRAINT objectif_ther_patient_fk
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE;
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table patients manquante, FK ignorée';
        END;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='objectif_ther_grille_fk') THEN
        BEGIN
            ALTER TABLE objectif_therapeutique
                ADD CONSTRAINT objectif_ther_grille_fk
                FOREIGN KEY (grille_id) REFERENCES grille_evaluation(id) ON DELETE CASCADE;
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table grille_evaluation manquante, FK ignorée';
        END;
    END IF;
END $$;

-- 4b. Table grille_version (après grille_evaluation)
CREATE TABLE IF NOT EXISTS grille_version (
    id SERIAL PRIMARY KEY,
    grille_id INTEGER NOT NULL,
    version_num INTEGER NOT NULL,
    domaines_config TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE NOT NULL,
    date_creation TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    date_modification TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_grille_version_grille ON grille_version(grille_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_grille_version_unique ON grille_version(grille_id, version_num);
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='grille_version_grille_fk') THEN
        BEGIN
            ALTER TABLE grille_version
                ADD CONSTRAINT grille_version_grille_fk
                FOREIGN KEY (grille_id) REFERENCES grille_evaluation(id) ON DELETE CASCADE;
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table grille_evaluation manquante, FK ignorée';
        END;
    END IF;
END $$;

-- 5. Trigger de mise à jour timestamp (facultatif si déjà géré par ORM)
-- (Désactivé ici; laisser SQLAlchemy gérer) 

-- 6. Vue synthèse évolution (optionnel)
-- Vue: supprimer d'abord pour éviter échec si structure ancienne
DROP VIEW IF EXISTS vue_cotation_evolution;
CREATE VIEW vue_cotation_evolution AS
SELECT
    cs.id,
    cs.seance_id,
    s.patient_id,
    cs.grille_id,
    cs.score_global,
    cs.pourcentage_reussite,
    COALESCE(cs.date_creation, NOW()) AS date_creation
FROM cotation_seance cs
JOIN seances s ON s.id = cs.seance_id;

-- 7. Correction: supprimer grille_version_id de cotation_seance si elle existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='cotation_seance' AND column_name='grille_version_id'
    ) THEN
        ALTER TABLE cotation_seance DROP COLUMN IF EXISTS grille_version_id;
        RAISE NOTICE 'Colonne grille_version_id supprimée de cotation_seance';
    END IF;
END $$;

-- 8. Correction: supprimer grille_version_id de objectif_therapeutique si elle existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='objectif_therapeutique' AND column_name='grille_version_id'
    ) THEN
        ALTER TABLE objectif_therapeutique DROP COLUMN IF EXISTS grille_version_id;
        RAISE NOTICE 'Colonne grille_version_id supprimée de objectif_therapeutique';
    END IF;
END $$;

-- 9. Vérifications rapides
-- SELECT * FROM grille_evaluation LIMIT 1;
-- SELECT * FROM cotation_seance LIMIT 1;
-- SELECT * FROM objectif_therapeutique LIMIT 1;