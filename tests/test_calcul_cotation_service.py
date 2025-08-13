from app.services.calcul_cotation_service import CalculCotationService

def test_calculer_score_global_simple():
    domaines = [
        {
            'nom': 'Engagement',
            'indicateurs': [
                {'nom': 'Attention', 'min': 0, 'max': 5},
                {'nom': 'Initiative', 'min': 0, 'max': 5}
            ]
        }
    ]
    scores = {
        'Engagement_Attention': 3,
        'Engagement_Initiative': 4
    }
    total, max_total, pct = CalculCotationService.calculer_score_global(domaines, scores)
    assert total == 7
    assert max_total == 10
    assert round(pct, 2) == 70.0


def test_calculer_score_global_ignore_invalide():
    domaines = [
        {
            'nom': 'Expression',
            'indicateurs': [
                {'nom': 'Vocale', 'min': 0, 'max': 4},
                {'nom': 'Corporelle', 'min': 0, 'max': 6}
            ]
        }
    ]
    scores = {
        'Expression_Vocale': 'non-num',
        'Expression_Corporelle': 5
    }
    total, max_total, pct = CalculCotationService.calculer_score_global(domaines, scores)
    assert total == 5
    assert max_total == 10
    assert round(pct, 1) == 50.0
