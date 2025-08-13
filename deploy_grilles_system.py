#!/usr/bin/env python3
"""
Script de déploiement du système de grilles de cotation.
À exécuter après le déploiement pour initialiser le système de grilles.
"""

import os
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.cotation import GrilleEvaluation
from app.services.cotation_service import CotationService


def deploy_grilles_system():
    """Déploie le système de grilles de cotation."""
    print("🎵 Déploiement du système de grilles Synchronie")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Créer les tables si elles n'existent pas
            print("📁 Création des tables...")
            db.create_all()
            print("✅ Tables créées avec succès")
            
            # 2. Vérifier que PatientGrille existe
            print("🔍 Vérification de la table PatientGrille...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'patient_grille' in tables:
                print("✅ Table PatientGrille existe")
            else:
                print("❌ Table PatientGrille manquante")
                return False
            
            # 3. Créer les grilles standards si elles n'existent pas
            print("📋 Vérification des grilles standards...")
            grilles_existantes = GrilleEvaluation.query.filter_by(est_standard=True).count()
            
            if grilles_existantes == 0:
                print("📝 Création des grilles standards...")
                
                # AMTA Standard
                CotationService.creer_grille_predefinie('amta')
                print("✅ Grille AMTA créée")
                
                # IMCAP-ND
                CotationService.creer_grille_predefinie('imcap_nd')
                print("✅ Grille IMCAP-ND créée")
                
                # Grille Gériatrique
                CotationService.creer_grille_predefinie('geriatrique')
                print("✅ Grille Gériatrique créée")
                
                # Grille Pédiatrique
                CotationService.creer_grille_predefinie('pediatrique')
                print("✅ Grille Pédiatrique créée")
                
                # Évaluation Rapide
                CotationService.creer_grille_predefinie('evaluation_rapide')
                print("✅ Grille Évaluation Rapide créée")
                
                print(f"✅ {5} grilles standards créées avec succès")
            else:
                print(f"✅ {grilles_existantes} grilles standards déjà présentes")
            
            # 4. Vérification finale
            print("🔍 Vérification finale...")
            total_grilles = GrilleEvaluation.query.count()
            grilles_standards = GrilleEvaluation.query.filter_by(est_standard=True).count()
            grilles_personnalisees = total_grilles - grilles_standards
            
            print("📊 Statistiques finales:")
            print(f"   • Total grilles: {total_grilles}")
            print(f"   • Grilles standards: {grilles_standards}")
            print(f"   • Grilles personnalisées: {grilles_personnalisees}")
            
            print("\n🎉 Déploiement du système de grilles terminé avec succès!")
            print("\n📋 Fonctionnalités disponibles:")
            print("   • Gestion des grilles via /grilles")
            print("   • Sélection de grilles à la création de patients")
            print("   • 5 grilles standards scientifiquement validées")
            print("   • Création de grilles personnalisées")
            print("   • Assignment de grilles multiples par patient")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du déploiement: {e}")
            return False


if __name__ == "__main__":
    success = deploy_grilles_system()
    sys.exit(0 if success else 1)
