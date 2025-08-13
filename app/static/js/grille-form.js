/**
 * Script pour la gestion des formulaires de grilles de cotation
 */

// Variables globales
let domaineCounter = 0;
let templates = {};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger les templates si on est en mode création
    if (document.getElementById('template-selection')) {
        chargerTemplates();
    }
    
    // Charger les domaines existants si on est en mode édition
    const grilleId = getGrilleId();
    if (grilleId) {
        chargerDomainesExistants(grilleId);
    }
    
    // Gérer la soumission du formulaire
    document.getElementById('grille-form').addEventListener('submit', soumettreFormulaire);
});

// Fonctions de navigation entre les types
function choisirType(type) {
    document.querySelectorAll('.template-choice').forEach(card => {
        card.style.display = 'none';
    });
    
    if (type === 'template') {
        document.getElementById('template-selection').style.display = 'block';
    } else if (type === 'custom') {
        document.getElementById('custom-form').style.display = 'block';
        // Ajouter un domaine par défaut
        if (domaineCounter === 0) {
            ajouterDomaine();
        }
    }
}

function retourChoixType() {
    document.getElementById('template-selection').style.display = 'none';
    document.querySelectorAll('.template-choice').forEach(card => {
        card.style.display = 'block';
    });
}

// Chargement des templates
async function chargerTemplates() {
    try {
        const response = await fetch('/grilles/api/templates');
        const result = await response.json();
        
        if (result.success) {
            templates = result.templates;
            afficherTemplates();
        } else {
            console.error('Erreur chargement templates:', result.message);
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

function afficherTemplates() {
    const container = document.getElementById('templates-list');
    container.innerHTML = '';
    
    Object.entries(templates).forEach(([key, template]) => {
        const templateCard = `
            <div class="col-md-6 mb-3">
                <div class="card h-100 border-primary">
                    <div class="card-body">
                        <h6 class="card-title">${template.nom}</h6>
                        <p class="card-text text-muted small">${template.description}</p>
                        ${template.reference_scientifique ? 
                            `<span class="badge bg-info mb-2">${template.reference_scientifique}</span>` : ''}
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">${template.domaines.length} domaines</small>
                            <button type="button" class="btn btn-primary btn-sm" 
                                    onclick="utiliserTemplate('${key}')">
                                Utiliser ce template
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += templateCard;
    });
}

async function utiliserTemplate(templateKey) {
    try {
        const response = await fetch('/grilles/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: 'template',
                template_key: templateKey
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = `/grilles/${result.grille_id}`;
        } else {
            alert('Erreur: ' + result.message);
        }
    } catch (error) {
        alert('Erreur lors de la création: ' + error.message);
    }
}

// Gestion des domaines
function ajouterDomaine() {
    const container = document.getElementById('domaines-container');
    const template = document.getElementById('domaine-template');
    const clone = template.content.cloneNode(true);
    
    // Personnaliser l'ID du domaine
    const domaineCard = clone.querySelector('.domaine-card');
    domaineCard.setAttribute('data-domaine-id', domaineCounter);
    
    // Couleurs prédéfinies pour les domaines
    const couleurs = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#6f42c1', '#20c997', '#fd7e14'];
    const couleurInput = clone.querySelector('.domaine-couleur');
    couleurInput.value = couleurs[domaineCounter % couleurs.length];
    
    container.appendChild(clone);
    
    // Ajouter un indicateur par défaut
    const nouveauDomaine = container.querySelector(`[data-domaine-id="${domaineCounter}"]`);
    ajouterIndicateur(nouveauDomaine.querySelector('.card-body button'));
    
    domaineCounter++;
}

function supprimerDomaine(button) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce domaine et tous ses indicateurs ?')) {
        button.closest('.domaine-card').remove();
    }
}

function ajouterIndicateur(button) {
    const container = button.parentElement.nextElementSibling;
    const template = document.getElementById('indicateur-template');
    const clone = template.content.cloneNode(true);
    
    container.appendChild(clone);
}

function supprimerIndicateur(button) {
    const indicateurRow = button.closest('.indicateur-row');
    const container = indicateurRow.parentElement;
    
    // Vérifier qu'il reste au moins un indicateur
    if (container.querySelectorAll('.indicateur-row').length > 1) {
        indicateurRow.remove();
    } else {
        alert('Un domaine doit contenir au moins un indicateur.');
    }
}

// Collecte des données du formulaire
function collecterDonnees() {
    const nom = document.getElementById('nom').value.trim();
    const description = document.getElementById('description').value.trim();
    
    if (!nom) {
        throw new Error('Le nom de la grille est obligatoire');
    }
    
    const domaines = [];
    const domaineCards = document.querySelectorAll('.domaine-card');
    
    if (domaineCards.length === 0) {
        throw new Error('La grille doit contenir au moins un domaine');
    }
    
    domaineCards.forEach(card => {
        const nomDomaine = card.querySelector('.domaine-nom').value.trim();
        const couleur = card.querySelector('.domaine-couleur').value;
        const descriptionDomaine = card.querySelector('.domaine-description').value.trim();
        
        if (!nomDomaine) {
            throw new Error('Tous les domaines doivent avoir un nom');
        }
        
        const indicateurs = [];
        const indicateurRows = card.querySelectorAll('.indicateur-row');
        
        if (indicateurRows.length === 0) {
            throw new Error(`Le domaine "${nomDomaine}" doit contenir au moins un indicateur`);
        }
        
        indicateurRows.forEach(row => {
            const nomIndicateur = row.querySelector('.indicateur-nom').value.trim();
            const min = parseInt(row.querySelector('.indicateur-min').value);
            const max = parseInt(row.querySelector('.indicateur-max').value);
            const unite = row.querySelector('.indicateur-unite').value.trim();
            
            if (!nomIndicateur) {
                throw new Error(`Tous les indicateurs du domaine "${nomDomaine}" doivent avoir un nom`);
            }
            
            if (isNaN(min) || isNaN(max) || min >= max) {
                throw new Error(`Valeurs min/max invalides pour l'indicateur "${nomIndicateur}"`);
            }
            
            indicateurs.push({
                nom: nomIndicateur,
                min: min,
                max: max,
                unite: unite || 'points'
            });
        });
        
        domaines.push({
            nom: nomDomaine,
            couleur: couleur,
            description: descriptionDomaine,
            indicateurs: indicateurs
        });
    });
    
    return {
        nom: nom,
        description: description,
        domaines: domaines
    };
}

// Soumission du formulaire
async function soumettreFormulaire(event) {
    event.preventDefault();
    
    try {
        const donnees = collecterDonnees();
        const grilleId = getGrilleId();
        
        const url = grilleId ? `/grilles/${grilleId}/update` : '/grilles/create';
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(donnees)
        });
        
        const result = await response.json();
        
        if (result.success) {
            const targetId = result.grille_id || grilleId;
            window.location.href = `/grilles/${targetId}`;
        } else {
            alert('Erreur: ' + result.message);
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
    }
}

// Utilitaires
function getGrilleId() {
    // Extraire l'ID de la grille depuis l'URL si on est en mode édition
    const match = window.location.pathname.match(/\/grilles\/(\d+)/);
    return match ? parseInt(match[1]) : null;
}

function annuler() {
    if (confirm('Êtes-vous sûr de vouloir annuler ? Les modifications non sauvegardées seront perdues.')) {
        window.location.href = '/grilles/';
    }
}

// Chargement des domaines existants pour l'édition
async function chargerDomainesExistants(grilleId) {
    try {
        const response = await fetch(`/grilles/${grilleId}`);
        // Cette fonction nécessiterait une API pour récupérer les détails de la grille
        // Pour l'instant, on la laisse vide car elle sera implémentée avec l'API grille details
    } catch (error) {
        console.error('Erreur chargement domaines existants:', error);
    }
}
