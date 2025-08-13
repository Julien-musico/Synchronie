-- Script minimal pour créer les tables de base
-- À exécuter AVANT le script complet

-- Vérifier les tables existantes
\dt

-- Créer seulement la table utilisateur de base si elle n'existe pas
CREATE TABLE IF NOT EXISTS utilisateur (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer la table musicothérapeute basée sur utilisateur
CREATE TABLE IF NOT EXISTS musicotherapeute (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER REFERENCES utilisateur(id),
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    specialisation TEXT,
    numero_adeli VARCHAR(20),
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer la table patient
CREATE TABLE IF NOT EXISTS patient (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE,
    sexe VARCHAR(1) CHECK (sexe IN ('M', 'F')),
    musicotherapeute_id INTEGER NOT NULL REFERENCES musicotherapeute(id),
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer la table seance
CREATE TABLE IF NOT EXISTS seance (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patient(id),
    date_seance DATE NOT NULL,
    duree INTEGER, -- en minutes
    type_seance VARCHAR(50),
    observations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vérification
SELECT 'Tables de base créées:' as status;
\dt
