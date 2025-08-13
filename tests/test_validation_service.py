import pytest
from app.services.validation_service import CotationValidator, ValidationError

def test_valider_domaine_valide():
    domaine = {
        'nom': 'Expression Musicale',
        'couleur': '#ff5722',
        'description': 'Capacité d\'expression créative',
        'indicateurs': [
            {'nom': 'Créativité', 'min': 0, 'max': 10, 'unite': 'points'},
            {'nom': 'Fluidité', 'min': 0, 'max': 5, 'unite': 'niveaux'}
        ]
    }
    resultat = CotationValidator.valider_domaine(domaine)
    assert resultat['nom'] == 'Expression Musicale'
    assert len(resultat['indicateurs']) == 2
    assert resultat['indicateurs'][0]['nom'] == 'Créativité'

def test_valider_domaine_nom_invalide():
    domaine = {'nom': 'X', 'indicateurs': [{'nom': 'Test', 'min': 0, 'max': 5}]}
    with pytest.raises(ValidationError, match="min 2 caractères"):
        CotationValidator.valider_domaine(domaine)

def test_valider_indicateur_limites_invalides():
    indicateur = {'nom': 'Test', 'min': 10, 'max': 5, 'unite': 'pts'}
    with pytest.raises(ValidationError, match="max doit être supérieure à min"):
        CotationValidator.valider_indicateur(indicateur)

def test_valider_grille_complete():
    domaines = [
        {
            'nom': 'Domaine A',
            'couleur': '#333',
            'description': 'Test A',
            'indicateurs': [{'nom': 'Ind1', 'min': 0, 'max': 5, 'unite': 'pts'}]
        },
        {
            'nom': 'Domaine B', 
            'couleur': '#666',
            'description': 'Test B',
            'indicateurs': [{'nom': 'Ind2', 'min': 0, 'max': 10, 'unite': 'pts'}]
        }
    ]
    resultat = CotationValidator.valider_grille_complete(domaines)
    assert len(resultat) == 2
    assert resultat[0]['nom'] == 'Domaine A'

def test_valider_scores_cotation():
    domaines = [
        {
            'nom': 'Expression',
            'indicateurs': [
                {'nom': 'Vocal', 'min': 0, 'max': 5},
                {'nom': 'Gestuel', 'min': 0, 'max': 10}
            ]
        }
    ]
    scores = {
        'Expression_Vocal': 3,
        'Expression_Gestuel': 7,
        'Expression_Inconnu': 2  # Score inattendu
    }
    scores_valides, erreurs = CotationValidator.valider_scores_cotation(scores, domaines)
    assert len(scores_valides) == 2
    assert len(erreurs) == 1
    assert 'Expression_Vocal' in scores_valides
    assert scores_valides['Expression_Vocal'] == 3.0
    assert 'Inconnu' in erreurs[0]

def test_valider_scores_hors_limites():
    domaines = [
        {
            'nom': 'Test',
            'indicateurs': [{'nom': 'Limite', 'min': 0, 'max': 5}]
        }
    ]
    scores = {'Test_Limite': 10}  # Hors limite max
    scores_valides, erreurs = CotationValidator.valider_scores_cotation(scores, domaines)
    assert len(scores_valides) == 0
    assert len(erreurs) == 1
    assert 'hors limites' in erreurs[0]
