-- Script pour vérifier et créer toutes les tables nécessaires
-- À exécuter sur Render PostgreSQL

-- 1. Vérifier les tables existantes
\dt

-- 2. Créer les tables de base si elles n'existent pas

-- Table musicotherapeute
CREATE TABLE IF NOT EXISTS musicotherapeute (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    telephone VARCHAR(20),
    specialisation TEXT,
    numero_adeli VARCHAR(20),
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table patient
CREATE TABLE IF NOT EXISTS patient (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE,
    sexe VARCHAR(1) CHECK (sexe IN ('M', 'F')),
    adresse TEXT,
    telephone VARCHAR(20),
    email VARCHAR(255),
    contact_urgence VARCHAR(255),
    pathologie TEXT,
    antecedents_medicaux TEXT,
    traitements_medicaux TEXT,
    objectifs_therapeutiques TEXT,
    musicotherapeute_id INTEGER NOT NULL REFERENCES musicotherapeute(id),
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table seance
CREATE TABLE IF NOT EXISTS seance (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patient(id),
    date_seance DATE NOT NULL,
    heure_debut TIME,
    duree INTEGER, -- en minutes
    type_seance VARCHAR(50),
    objectifs_seance TEXT,
    deroulement TEXT,
    observations TEXT,
    score_engagement INTEGER CHECK (score_engagement >= 0 AND score_engagement <= 10),
    fichier_audio VARCHAR(255),
    transcription TEXT,
    synthese_ia TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les tables de base
CREATE INDEX IF NOT EXISTS ix_patient_musicotherapeute_id ON patient(musicotherapeute_id);
CREATE INDEX IF NOT EXISTS ix_seance_patient_id ON seance(patient_id);
CREATE INDEX IF NOT EXISTS ix_seance_date ON seance(date_seance);

-- 3. Maintenant créer les tables de cotation

-- Table des grilles d'évaluation
CREATE TABLE IF NOT EXISTS grille_evaluation (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(200) NOT NULL,
    description TEXT,
    type_grille VARCHAR(50) NOT NULL,
    reference_scientifique VARCHAR(100),
    domaines_config TEXT NOT NULL,
    musicotherapeute_id INTEGER REFERENCES musicotherapeute(id),
    active BOOLEAN DEFAULT TRUE,
    publique BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les grilles d'évaluation
CREATE INDEX IF NOT EXISTS ix_grille_evaluation_musicotherapeute_id ON grille_evaluation(musicotherapeute_id);
CREATE INDEX IF NOT EXISTS ix_grille_evaluation_active ON grille_evaluation(active);
CREATE INDEX IF NOT EXISTS ix_grille_evaluation_publique ON grille_evaluation(publique);

-- Table des cotations de séance
CREATE TABLE IF NOT EXISTS cotation_seance (
    id SERIAL PRIMARY KEY,
    seance_id INTEGER NOT NULL REFERENCES seance(id),
    grille_id INTEGER NOT NULL REFERENCES grille_evaluation(id),
    scores_detailles TEXT NOT NULL,
    score_global FLOAT,
    score_max_possible FLOAT,
    pourcentage_reussite FLOAT,
    observations_cotation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contrainte unique pour éviter les doublons
    UNIQUE(seance_id, grille_id)
);

-- Index pour les cotations de séance
CREATE INDEX IF NOT EXISTS ix_cotation_seance_seance_id ON cotation_seance(seance_id);
CREATE INDEX IF NOT EXISTS ix_cotation_seance_grille_id ON cotation_seance(grille_id);

-- Table des objectifs thérapeutiques
CREATE TABLE IF NOT EXISTS objectif_therapeutique (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patient(id),
    grille_id INTEGER NOT NULL REFERENCES grille_evaluation(id),
    domaine_cible VARCHAR(100) NOT NULL,
    objectif_description TEXT NOT NULL,
    criteres_reussite TEXT,
    echeance_prevue DATE,
    statut VARCHAR(20) DEFAULT 'en_cours',
    notes_progression TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les objectifs thérapeutiques
CREATE INDEX IF NOT EXISTS ix_objectif_therapeutique_patient_id ON objectif_therapeutique(patient_id);
CREATE INDEX IF NOT EXISTS ix_objectif_therapeutique_grille_id ON objectif_therapeutique(grille_id);
CREATE INDEX IF NOT EXISTS ix_objectif_therapeutique_statut ON objectif_therapeutique(statut);

-- 4. Triggers pour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour toutes les tables
CREATE TRIGGER update_musicotherapeute_updated_at 
    BEFORE UPDATE ON musicotherapeute 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patient_updated_at 
    BEFORE UPDATE ON patient 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seance_updated_at 
    BEFORE UPDATE ON seance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_grille_evaluation_updated_at 
    BEFORE UPDATE ON grille_evaluation 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cotation_seance_updated_at 
    BEFORE UPDATE ON cotation_seance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_objectif_therapeutique_updated_at 
    BEFORE UPDATE ON objectif_therapeutique 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5. Insérer des grilles prédéfinies
INSERT INTO grille_evaluation (nom, description, type_grille, reference_scientifique, domaines_config, publique, active)
VALUES 
    ('AMTA - Grille Standard', 
     'Grille de l''Association Américaine de Musicothérapie (7 domaines, 28 indicateurs)', 
     'standard', 
     'AMTA',
     '[{"nom":"Engagement Musical","couleur":"#3498db","description":"Participation active aux activités musicales","indicateurs":[{"nom":"Attention soutenue","min":0,"max":5,"unite":"points"},{"nom":"Initiative musicale","min":0,"max":5,"unite":"points"},{"nom":"Persévérance","min":0,"max":5,"unite":"points"},{"nom":"Exploration sonore","min":0,"max":5,"unite":"points"}]},{"nom":"Expression Émotionnelle","couleur":"#e67e22","description":"Capacité à exprimer et réguler les émotions","indicateurs":[{"nom":"Expression spontanée","min":0,"max":5,"unite":"points"},{"nom":"Régulation émotionnelle","min":0,"max":5,"unite":"points"},{"nom":"Reconnaissance émotions","min":0,"max":5,"unite":"points"},{"nom":"Empathie musicale","min":0,"max":5,"unite":"points"}]}]',
     TRUE,
     TRUE
    ),
    ('IMCAP-ND - Troubles Autistiques',
     'Échelle spécialisée pour troubles du spectre autistique (fiabilité 98%)',
     'standard',
     'IMCAP-ND',
     '[{"nom":"Engagement Social","couleur":"#3498db","description":"Interaction et connection sociale","indicateurs":[{"nom":"Regard dirigé","min":0,"max":4,"unite":"niveau"},{"nom":"Sourire social","min":0,"max":4,"unite":"niveau"},{"nom":"Imitation spontanée","min":0,"max":4,"unite":"niveau"},{"nom":"Jeu partagé","min":0,"max":4,"unite":"niveau"}]}]',
     TRUE,
     TRUE
    )
ON CONFLICT DO NOTHING;

-- 6. Vérification finale
SELECT 'Tables créées:' as info;
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('musicotherapeute', 'patient', 'seance', 'grille_evaluation', 'cotation_seance', 'objectif_therapeutique')
ORDER BY tablename;

SELECT 'Grilles disponibles:' as info;
SELECT nom, reference_scientifique FROM grille_evaluation WHERE publique = TRUE;
