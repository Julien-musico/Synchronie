#!/usr/bin/env python3
"""
Script de correction rapide pour la production.
Corrige les problèmes de compatibilité de l'interface de cotation.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.cotation import GrilleEvaluation

def fix_cotation_production():
    """Corrige les problèmes de production pour l'interface de cotation."""
    print("🔧 Correction de l'interface de cotation pour la production")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Vérifier les colonnes existantes dans GrilleEvaluation
            print("📋 Vérification de la structure de GrilleEvaluation...")
            
            # Test des attributs problématiques
            try:
                test_query = GrilleEvaluation.query.filter(
                    GrilleEvaluation.active.is_(True)
                ).count()
                print(f"✅ Colonne 'active' existe - {test_query} grilles actives")
            except Exception as e:
                print(f"❌ Colonne 'active' manquante: {e}")
                
            try:
                test_query = GrilleEvaluation.query.filter(
                    GrilleEvaluation.publique.is_(True)
                ).count()
                print(f"✅ Colonne 'publique' existe - {test_query} grilles publiques")
            except Exception as e:
                print(f"❌ Colonne 'publique' manquante: {e}")
            
            # 2. Test de requête robuste
            print("\n🔍 Test de requête robuste...")
            try:
                grilles = GrilleEvaluation.query.all()
                print(f"✅ {len(grilles)} grilles trouvées en total")
                
                if grilles:
                    grille = grilles[0]
                    print(f"   • Première grille: {grille.nom}")
                    print(f"   • Description: {grille.description or 'Aucune'}")
                    print(f"   • Type: {getattr(grille, 'type_grille', 'Non défini')}")
                    
                    # Test de l'attribut domaines
                    try:
                        domaines = grille.domaines
                        print(f"   • Domaines: {len(domaines) if domaines else 0}")
                    except Exception as e:
                        print(f"   • Erreur domaines: {e}")
            except Exception as e:
                print(f"❌ Erreur lors de la requête de base: {e}")
            
            # 3. Test de création de grilles si aucune n'existe
            if not grilles:
                print("\n📝 Aucune grille trouvée, création d'une grille de test...")
                try:
                    grille_test = GrilleEvaluation(
                        nom="Test Cotation",
                        description="Grille de test pour valider l'interface",
                        type_grille="standard",
                        domaines_config='[{"nom":"Test","indicateurs":[{"nom":"Indicateur test","min":0,"max":5}]}]'
                    )
                    db.session.add(grille_test)
                    db.session.commit()
                    print("✅ Grille de test créée avec succès")
                except Exception as e:
                    print(f"❌ Erreur lors de la création de grille test: {e}")
                    db.session.rollback()
            
            print("\n🎉 Diagnostic terminé!")
            print("\n📋 Actions recommandées:")
            print("   1. Vérifier que les colonnes 'active' et 'publique' existent")
            print("   2. Utiliser le template simple en cas de problème")
            print("   3. Déployer les corrections sur Render.com")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            return False

if __name__ == "__main__":
    success = fix_cotation_production()
    sys.exit(0 if success else 1)
