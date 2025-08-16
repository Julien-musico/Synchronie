# Guide pour patcher la base de données sur Render

## Étapes pour appliquer le patch via le shell Render

### 1. Accéder au shell Render
1. Allez sur le dashboard Render : https://dashboard.render.com
2. Sélectionnez votre service Synchronie
3. Cliquez sur l'onglet "Shell" dans le menu de gauche
4. Cliquez sur "Launch Shell" pour ouvrir un terminal

### 2. Vérifier l'environnement
```bash
# Vérifier que vous êtes dans le bon répertoire
pwd
ls -la

# Vérifier que DATABASE_URL est définie
echo $DATABASE_URL
```

### 3. Appliquer le patch
```bash
# Option 1: Utiliser le script bash
chmod +x patch_db.sh
./patch_db.sh

# Option 2: Exécuter directement avec psql
psql "$DATABASE_URL" -f sql/schema_patch.sql

# Option 3: Exécuter les commandes une par une
psql "$DATABASE_URL" -c "ALTER TABLE cotation_seance DROP COLUMN IF EXISTS grille_version_id;"
psql "$DATABASE_URL" -c "ALTER TABLE objectif_therapeutique DROP COLUMN IF EXISTS grille_version_id;"
```

### 4. Vérifier que le patch a fonctionné
```bash
# Vérifier que les colonnes problématiques ont été supprimées
psql "$DATABASE_URL" -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'cotation_seance' AND column_name = 'grille_version_id';"

# Si aucun résultat n'est retourné, c'est que la colonne a été supprimée avec succès
```

### 5. Redémarrer l'application
Après avoir appliqué le patch, redémarrez votre service Render :
- Retournez sur le dashboard
- Cliquez sur "Manual Deploy" > "Deploy latest commit"
- Ou utilisez le bouton "Restart"

## Commandes de diagnostic
```bash
# Voir toutes les colonnes de la table cotation_seance
psql "$DATABASE_URL" -c "\d cotation_seance"

# Voir toutes les colonnes de la table objectif_therapeutique  
psql "$DATABASE_URL" -c "\d objectif_therapeutique"

# Tester une requête simple
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM cotation_seance;"
```

## Résolution de problèmes

### Si psql n'est pas disponible
```bash
# Installer psql (si nécessaire)
apt-get update && apt-get install -y postgresql-client
```

### Si le fichier SQL n'est pas trouvé
```bash
# Créer le fichier directement dans le shell
cat > schema_patch.sql << 'EOF'
-- Section 7: Supprimer grille_version_id de cotation_seance si elle existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cotation_seance' 
        AND column_name = 'grille_version_id'
    ) THEN
        ALTER TABLE cotation_seance DROP COLUMN grille_version_id;
        RAISE NOTICE 'Colonne grille_version_id supprimée de cotation_seance';
    ELSE
        RAISE NOTICE 'Colonne grille_version_id n''existe pas dans cotation_seance';
    END IF;
END $$;

-- Section 8: Supprimer grille_version_id de objectif_therapeutique si elle existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'objectif_therapeutique' 
        AND column_name = 'grille_version_id'
    ) THEN
        ALTER TABLE objectif_therapeutique DROP COLUMN grille_version_id;
        RAISE NOTICE 'Colonne grille_version_id supprimée de objectif_therapeutique';
    ELSE
        RAISE NOTICE 'Colonne grille_version_id n''existe pas dans objectif_therapeutique';
    END IF;
END $$;
EOF

# Puis exécuter
psql "$DATABASE_URL" -f schema_patch.sql
```
