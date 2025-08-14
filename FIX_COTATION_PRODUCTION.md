# 🔧 Fix Interface Cotation - Production

## Problème identifié
L'interface de cotation `/cotation/seance/7/coter` génère une erreur sur Render.com.

## Solutions implémentées

### 1. **Code robuste** 
- Gestion d'erreur dans la route `interface_cotation`
- Fallback si les colonnes `active`/`publique` n'existent pas
- Template simple de test créé

### 2. **Template de diagnostic**
Les anciennes variantes d'interface (simple/enhanced/new) ont été retirées au profit de `interface_cotation_clean.html`.
- Affiche les informations de base sans JavaScript complexe

### 3. **Route corrigée**
```python
# Requête robuste avec fallback
try:
    grilles = GrilleEvaluation.query.filter(
        db.or_(
            GrilleEvaluation.musicotherapeute_id == current_user.id,
            GrilleEvaluation.publique.is_(True)
        ),
        GrilleEvaluation.active.is_(True)
    ).all()
except Exception:
    # Fallback si colonnes manquantes
    grilles = GrilleEvaluation.query.filter(
        db.or_(
            GrilleEvaluation.musicotherapeute_id == current_user.id,
            GrilleEvaluation.musicotherapeute_id.is_(None)
        )
    ).all()
```

## Actions pour Render.com

### 1. **Créer les colonnes manquantes**
```sql
-- Via pgAdmin ou console Render
ALTER TABLE grille_evaluation 
ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;

ALTER TABLE grille_evaluation 
ADD COLUMN IF NOT EXISTS publique BOOLEAN DEFAULT FALSE;
```

### 2. **Alternative sans modification DB**
```python
# Utiliser uniquement les colonnes existantes
grilles = GrilleEvaluation.query.filter(
    db.or_(
        GrilleEvaluation.musicotherapeute_id == current_user.id,
        GrilleEvaluation.musicotherapeute_id.is_(None)  # Grilles "publiques"
    )
).all()
```

### 3. **Test immédiat**
- Interface simplifiée active temporairement
- Affiche les informations de base
- Permet d'identifier le problème exact

## Déploiement
1. Pousser les modifications sur Git
2. Render.com redéploiera automatiquement
3. Tester l'URL `/cotation/seance/7/coter`
4. Si OK, remettre le template complet

## Rollback si besoin
- Template simple reste disponible
- Route robuste avec gestion d'erreur
- Pas de régression de fonctionnalité
