#!/usr/bin/env python3
"""Test de la fonctionnalité de cotation simplifiée"""

def test_cotation_simple():
    """Test unitaire de la sauvegarde simplifiée"""
    
    # Données de test simulées
    scores_test = {
        "Communication verbale": 3,
        "Participation active": 4,
        "Expression émotionnelle": 2,
        "Interaction sociale": 3
    }
    
    observations_test = "Patient très réceptif lors de cette séance. Amélioration notable de la communication."
    
    print("🧪 TEST DE COTATION SIMPLIFIÉE")
    print("=" * 40)
    
    print(f"\n📊 Scores de test:")
    for indicateur, score in scores_test.items():
        print(f"  • {indicateur}: {score}/5")
    
    print(f"\n📝 Observations: {observations_test}")
    
    # Calcul manuel du score global
    total = sum(scores_test.values())
    nb_indicateurs = len(scores_test)
    score_global = total / nb_indicateurs
    score_max = nb_indicateurs * 5
    pourcentage = (total / score_max) * 100
    
    print(f"\n🎯 Calculs attendus:")
    print(f"  • Score global: {score_global:.1f}/5")
    print(f"  • Score max possible: {score_max}")
    print(f"  • Pourcentage: {pourcentage:.1f}%")
    
    print(f"\n✅ Structure JSON des scores:")
    import json
    print(json.dumps(scores_test, indent=2, ensure_ascii=False))
    
    return scores_test, observations_test

if __name__ == '__main__':
    test_cotation_simple()
