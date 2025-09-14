-- Vérification structure des tables patient et patient_grille
-- Exécuter dans psql ou pgAdmin

\echo '--- Table patients ---'
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'patients'
ORDER BY ordinal_position;

\echo 'Clés & index patients'
SELECT indexname, indexdef FROM pg_indexes WHERE tablename='patients';

\echo '--- Table patient_grille ---'
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'patient_grille'
ORDER BY ordinal_position;

\echo 'Clés & index patient_grille'
SELECT indexname, indexdef FROM pg_indexes WHERE tablename='patient_grille';

\echo 'Contraintes FK patient_grille'
SELECT tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'patient_grille' AND tc.constraint_type='FOREIGN KEY';

\echo '--- Orphelins patient_grille (devraient être 0) ---'
SELECT pg.patient_id, pg.grille_id
FROM patient_grille pg
LEFT JOIN patients p ON p.id = pg.patient_id
WHERE p.id IS NULL;

\echo '--- Doublons potentiels patient_grille ---'
SELECT patient_id, grille_id, COUNT(*)
FROM patient_grille
GROUP BY patient_id, grille_id
HAVING COUNT(*) > 1;

\echo '--- Présence colonnes attendues ---'
-- user_id dans patients
SELECT 'patients.user_id existe' AS check, COUNT(*)>0 AS ok
FROM information_schema.columns
WHERE table_name='patients' AND column_name='user_id';

-- priorite et active dans patient_grille
SELECT 'patient_grille.priorite existe' AS check, COUNT(*)>0 AS ok
FROM information_schema.columns
WHERE table_name='patient_grille' AND column_name='priorite';

SELECT 'patient_grille.active existe' AS check, COUNT(*)>0 AS ok
FROM information_schema.columns
WHERE table_name='patient_grille' AND column_name='active';
