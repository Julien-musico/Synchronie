@echo off
REM Script pour patcher la base de données sur Render
REM Usage: patch_db.bat

echo 🔧 Début du patch de base de données...

REM Vérifier que DATABASE_URL est définie
if "%DATABASE_URL%"=="" (
    echo ❌ Variable d'environnement DATABASE_URL non définie
    exit /b 1
)

echo ✅ Connexion à la base de données...

REM Exécuter le patch SQL
psql "%DATABASE_URL%" -f sql/schema_patch.sql

if %ERRORLEVEL% EQU 0 (
    echo ✅ Patch appliqué avec succès!
    
    REM Vérifier que les colonnes problématiques ont été supprimées
    echo 🔍 Vérification des modifications...
    
    psql "%DATABASE_URL%" -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'cotation_seance' AND column_name = 'grille_version_id';"
    
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Vérification terminée
    ) else (
        echo ⚠️ Erreur lors de la vérification
    )
    
    echo 🎉 Patch de base de données terminé!
) else (
    echo ❌ Erreur lors de l'application du patch
    exit /b 1
)
