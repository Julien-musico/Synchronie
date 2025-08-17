-- Script SQL exhaustif pour l’import manuel des grilles standardisées
-- À utiliser dans pgAdmin

-- Exemple pour la grille AMTA
INSERT INTO grille (nom, description, type_grille, reference_scientifique) VALUES
('AMTA Assessment Tools', 'Outils d’évaluation recommandés par l’American Music Therapy Association (AMTA) - 7 domaines, 28 indicateurs.', 'standardisée', 'AMTA');
-- Récupérer l'id de la grille créée (ex: grille_id = 1)

-- Domaine : Musicalité
INSERT INTO domaine (nom, description) VALUES ('Musicalité', NULL);
-- id_domaine = ?
INSERT INTO indicateur (nom, description) VALUES ('Rythme', NULL);
-- id_indicateur = ?
INSERT INTO domaine_indicateur (domaine_id, indicateur_id) VALUES (id_domaine, id_indicateur);
INSERT INTO indicateur (nom, description) VALUES ('Mélodie', NULL);
INSERT INTO indicateur (nom, description) VALUES ('Harmonie', NULL);
INSERT INTO indicateur (nom, description) VALUES ('Improvisation', NULL);
-- Répéter domaine_indicateur pour chaque indicateur
INSERT INTO grille_domaine (grille_id, domaine_id) VALUES (grille_id, id_domaine);

-- Domaine : Social
INSERT INTO domaine (nom, description) VALUES ('Social', NULL);
INSERT INTO indicateur (nom, description) VALUES ('Interaction sociale', NULL);
INSERT INTO indicateur (nom, description) VALUES ('Communication verbale', NULL);
INSERT INTO indicateur (nom, description) VALUES ('Communication non verbale', NULL);
INSERT INTO indicateur (nom, description) VALUES ('Travail en groupe', NULL);
-- ...
-- Répéter pour tous les domaines et indicateurs

-- Répéter la structure pour chaque grille (PANSS, MT-SAS, MRS, IMTAP, IMCAP-ND, IAP, GDS, EMTC, CARS)
-- Pour chaque grille, adapter nom, description, domaines, indicateurs, et liens

-- Les IDs sont à récupérer via pgAdmin après chaque insertion
-- Ou utiliser RETURNING id si tu fais les insertions une à une

-- Ce fichier est un modèle, je peux le compléter avec toutes les grilles et tous les indicateurs si tu le souhaites
