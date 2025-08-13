-- Script SQL pour créer les tables de cotation thérapeutique
-- À exécuter sur la base de données PostgreSQL de production

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

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Appliquer le trigger aux tables
DROP TRIGGER IF EXISTS update_grille_evaluation_updated_at ON grille_evaluation;
CREATE TRIGGER update_grille_evaluation_updated_at 
    BEFORE UPDATE ON grille_evaluation 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_cotation_seance_updated_at ON cotation_seance;
CREATE TRIGGER update_cotation_seance_updated_at 
    BEFORE UPDATE ON cotation_seance 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_objectif_therapeutique_updated_at ON objectif_therapeutique;
CREATE TRIGGER update_objectif_therapeutique_updated_at 
    BEFORE UPDATE ON objectif_therapeutique 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insérer quelques grilles prédéfinies pour commencer
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

-- Vérification des tables créées
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('grille_evaluation', 'cotation_seance', 'objectif_therapeutique')
ORDER BY tablename;
