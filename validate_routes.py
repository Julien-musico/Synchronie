#!/usr/bin/env python3
"""
Validation des URLs et routes dans l'application.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def validate_routes():
    """Valide que toutes les routes importantes existent."""
    print("🔍 Validation des routes de l'application")
    print("=" * 45)
    
    app = create_app()
    
    with app.app_context():
        # Récupérer toutes les routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': rule.rule
            })
        
        # Routes critiques à vérifier
        critical_routes = [
            'patients.view_patient',
            'patients.list_patients',
            'patients.edit_patient',
            'seances.view_seance',
            'seances.list_seances',
            'cotation_bp.interface_cotation',
            'grilles.list_grilles',
            'main.dashboard'
        ]
        
        print("📋 Vérification des routes critiques:")
        for route_name in critical_routes:
            found = any(r['endpoint'] == route_name for r in routes)
            status = "✅" if found else "❌"
            print(f"   {status} {route_name}")
            
            if found:
                route_info = next(r for r in routes if r['endpoint'] == route_name)
                print(f"      → {route_info['rule']} {route_info['methods']}")
        
        print(f"\n📊 Total des routes: {len(routes)}")
        
        # Rechercher les routes patients
        print("\n👥 Routes patients disponibles:")
        patient_routes = [r for r in routes if 'patients' in r['endpoint']]
        for route in patient_routes:
            print(f"   • {route['endpoint']} → {route['rule']}")
        
        # Rechercher les routes cotation
        print("\n📝 Routes cotation disponibles:")
        cotation_routes = [r for r in routes if 'cotation' in r['endpoint']]
        for route in cotation_routes:
            print(f"   • {route['endpoint']} → {route['rule']}")
        
        print("\n🎉 Validation terminée!")
        return True


if __name__ == "__main__":
    try:
        validate_routes()
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        sys.exit(1)
