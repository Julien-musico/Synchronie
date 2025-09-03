-- Script SQL pour lier chaque indicateur à son domaine pertinent
-- Table de liaison : domaine_indicateur (id SERIAL PRIMARY KEY, domaine_id INT, indicateur_id INT)
-- Remplace les IDs de domaine par ceux de ta table

-- Exemple de cartographie (à adapter selon tes besoins)
-- Social : 3
-- Émotionnel : 5
-- Sensoriel : 7
-- Bien-être : 13
-- Expression : 14
-- Engagement : 21
-- Communication : 24
-- Motricité : 27
-- Cognition : 28
-- Autonomie : 30
-- Créativité : 31
-- Interaction : 34
-- Relations sociales : 51
-- Relation à la musique : 100

-- Pour chaque indicateur, lier à son domaine
-- Exemple :
INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 3, id FROM indicateur WHERE nom IN ('Interaction sociale', 'Travail en groupe', 'Collaboration', 'Passivité sociale', 'Retrait social', 'Initiative sociale', 'Réponse sociale', 'Relations sociales', 'Contact visuel')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 5, id FROM indicateur WHERE nom IN ('Expression émotionnelle', 'Gestion des émotions', 'Reconnaissance des émotions', 'Régulation émotionnelle', 'Anxiété', 'Dépression', 'Tristesse', 'Joie', 'Irritabilité', 'Stabilité émotionnelle', 'Manifestation des émotions', 'Réaction émotionnelle', 'Expression verbale des émotions')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 7, id FROM indicateur WHERE nom IN ('Perception auditive', 'Perception visuelle', 'Perception tactile', 'Intégration sensorielle', 'Réponse sensorielle', 'Réceptivité auditive', 'Attention à la musique', 'Réceptivité musicale', 'Discrimination sonore', 'Sensibilité sensorielle', 'Intégration multisensorielle', 'Réactivité aux stimuli')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 13, id FROM indicateur WHERE nom IN ('Satisfaction', 'Implication', 'Intérêt pour la séance', 'Détente', 'Réduction du stress', 'Sentiment de sécurité', 'Satisfaction personnelle', 'Bien-être', 'Réduction de l’anxiété', 'Amélioration de l’humeur', 'Sentiment d’appartenance', 'Vitalité')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 14, id FROM indicateur WHERE nom IN ('Expression verbale', 'Expression corporelle', 'Expression personnelle', 'Authenticité', 'Spontanéité', 'Expression non verbale', 'Verbalisation', 'Clarté du discours', 'Expression verbale des émotions')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 21, id FROM indicateur WHERE nom IN ('Engagement musical', 'Participation active', 'Implication', 'Initiative musicale', 'Initiative personnelle', 'Initiative comportementale', 'Initiative créative', 'Initiative sociale', 'Initiative communicative', 'Initiatives sociales')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 24, id FROM indicateur WHERE nom IN ('Communication verbale', 'Communication non verbale', 'Initiative communicative', 'Compréhension verbale', 'Compréhension orale', 'Utilisation du langage', 'Initiation de la communication', 'Réponse aux sollicitations', 'Adaptation du registre')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 27, id FROM indicateur WHERE nom IN ('Motricité fine', 'Motricité globale', 'Coordination', 'Endurance', 'Mobilité', 'Gestuelle', 'Précision des mouvements', 'Rythme moteur', 'Coordination motrice', 'Gestion des comportements', 'Troubles de la motricité')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 28, id FROM indicateur WHERE nom IN ('Attention', 'Mémoire', 'Résolution de problèmes', 'Planification', 'Compréhension', 'Orientation spatio-temporelle', 'Fonctions exécutives', 'Raisonnement', 'Flexibilité cognitive', 'Vitesse de traitement', 'Gestion du temps', 'Organisation personnelle', 'Autonomie dans les tâches', 'Responsabilisation', 'Troubles du jugement', 'Troubles de la pensée', 'Troubles du contrôle')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 30, id FROM indicateur WHERE nom IN ('Autonomie', 'Confiance en soi', 'Estime de soi', 'Adaptation', 'Adaptation au changement', 'Adaptation aux changements', 'Soin personnel', 'Autonomie dans les tâches')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 31, id FROM indicateur WHERE nom IN ('Créativité', 'Originalité', 'Imagination', 'Production artistique', 'Prise de risque créative', 'Flexibilité créative', 'Création musicale', 'Exploration sonore', 'Improvisation', 'Spontanéité')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 34, id FROM indicateur WHERE nom IN ('Interaction sociale', 'Interaction musicale', 'Réponse aux autres', 'Réponse à autrui', 'Interaction', 'Collaboration', 'Travail en groupe', 'Prise de tour de parole', 'Gestion des conflits', 'Adaptation au groupe')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 51, id FROM indicateur WHERE nom IN ('Relations sociales', 'Contact visuel', 'Passivité sociale', 'Retrait social', 'Qualité des relations', 'Isolement')
ON CONFLICT DO NOTHING;

INSERT INTO domaine_indicateur (domaine_id, indicateur_id)
SELECT 100, id FROM indicateur WHERE nom IN ('Engagement musical', 'Réceptivité musicale', 'Création musicale', 'Interprétation', 'Réaction émotionnelle à la musique', 'Attention musicale', 'Réponse à la musique', 'Participation musicale', 'Relation à la musique')
ON CONFLICT DO NOTHING;

-- À compléter selon tes besoins pour les autres domaines ou indicateurs spécifiques
