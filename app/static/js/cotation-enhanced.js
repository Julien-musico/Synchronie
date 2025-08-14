/**
 * SYNCHRONIE - Interface Cotation Enhanced
 * JavaScript pour une expérience utilisateur optimale
 */

class CotationInterface {
    constructor() {
        this.currentGrilleId = null;
        this.currentScores = {};
        this.totalIndicateurs = 0;
        this.indicateursCotes = 0;
        this.seanceId = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupAnimations();
        this.loadSeanceData();
    }
    
    setupEventListeners() {
        // Sélection de grille
        const grilleRadios = document.querySelectorAll('.grille-radio');
        const btnContinuer = document.getElementById('btn-continuer');
        
        grilleRadios.forEach(radio => {
            radio.addEventListener('change', (e) => this.onGrilleSelection(e));
        });
        
        if (btnContinuer) {
            btnContinuer.addEventListener('click', () => this.continueToEvaluation());
        }
        
        // Boutons d'action
        const btnSave = document.getElementById('btn-save');
        if (btnSave) {
            btnSave.addEventListener('click', () => this.saveCotation());
        }
        
        // Observations
        const observations = document.getElementById('observations');
        if (observations) {
            observations.addEventListener('input', this.debounce(() => {
                this.updateSaveButtonState();
            }, 300));
        }
        
        // Raccourcis clavier
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }
    
    loadSeanceData() {
        // Récupérer l'ID de la séance depuis le template
        const seanceElement = document.querySelector('[data-seance-id]');
        if (seanceElement) {
            this.seanceId = parseInt(seanceElement.dataset.seanceId);
        }
    }
    
    onGrilleSelection(event) {
        if (event.target.checked) {
            this.currentGrilleId = parseInt(event.target.value);
            const btnContinuer = document.getElementById('btn-continuer');
            btnContinuer.disabled = false;
            
            // Animation de sélection
            document.querySelectorAll('.grille-card').forEach(card => {
                card.classList.remove('animate__pulse');
            });
            
            event.target.closest('.grille-card').classList.add('animate__animated', 'animate__pulse');
            
            // Feedback visuel
            this.showFeedback('Grille sélectionnée', 'success', 2000);
        }
    }
    
    continueToEvaluation() {
        if (!this.currentGrilleId) return;
        
        const grilleSection = document.getElementById('grille-selection-section');
        const cotationInterface = document.getElementById('cotation-interface');
        
        // Animation de transition
        grilleSection.classList.add('animate__animated', 'animate__fadeOutUp');
        
        setTimeout(() => {
            grilleSection.style.display = 'none';
            this.loadGrilleData(this.currentGrilleId);
            cotationInterface.style.display = 'block';
            cotationInterface.classList.add('animate__animated', 'animate__fadeInUp');
            
            // Scroll vers l'interface
            cotationInterface.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 300);
    }
    
    async loadGrilleData(grilleId) {
        this.showLoading(true);
        
        try {
            const response = await fetch(`/cotation/grille/${grilleId}/domaines`);
            const data = await response.json();
            
            if (data.success) {
                this.renderDomaines(data.domaines);
                this.setupProgressTracking();
                this.showFeedback('Grille chargée avec succès', 'success', 3000);
            } else {
                throw new Error(data.message || 'Erreur lors du chargement de la grille');
            }
        } catch (error) {
            console.error('Erreur lors du chargement de la grille:', error);
            this.showAlert('Erreur lors du chargement de la grille: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    renderDomaines(domaines) {
        const container = document.getElementById('domaines-container');
        container.innerHTML = '';
        
        this.totalIndicateurs = 0;
        
        domaines.forEach((domaine, index) => {
            this.totalIndicateurs += domaine.indicateurs.length;
            const domaineElement = this.createDomaineElement(domaine, index);
            container.appendChild(domaineElement);
        });
        
        this.updateProgressDisplay();
        this.initializeSliders();
    }
    
    createDomaineElement(domaine, index) {
        const domaineDiv = document.createElement('div');
        domaineDiv.className = 'domaine-section animate__animated animate__fadeInUp';
        domaineDiv.style.animationDelay = `${index * 0.1}s`;
        
        domaineDiv.innerHTML = `
            <div class="domaine-header">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="domaine-title">
                        <i class="bi bi-grid-3x3-gap me-2"></i>
                        ${this.sanitizeHtml(domaine.nom)}
                    </h6>
                    <span class="domaine-score-badge" id="score-domaine-${domaine.id}">0%</span>
                </div>
                ${domaine.description ? `<p class="mt-2 mb-0 opacity-75 small">${this.sanitizeHtml(domaine.description)}</p>` : ''}
            </div>
            <div class="domaine-content">
                ${domaine.indicateurs.map(indicateur => this.createIndicateurHtml(indicateur, domaine.id)).join('')}
            </div>
        `;
        
        return domaineDiv;
    }
    
    createIndicateurHtml(indicateur, domaineId) {
        return `
            <div class="indicateur-item">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="flex-grow-1">
                        <div class="indicateur-label">${this.sanitizeHtml(indicateur.nom)}</div>
                        ${indicateur.description ? `<div class="indicateur-description">${this.sanitizeHtml(indicateur.description)}</div>` : ''}
                    </div>
                    <div class="indicateur-value-display" id="value-${indicateur.id}">0</div>
                </div>
                <div class="slider-container">
                    <div id="slider-${indicateur.id}" class="slider" 
                         data-indicateur-id="${indicateur.id}"
                         data-domaine-id="${domaineId}"
                         data-poids="${indicateur.poids || 1}"></div>
                    <div class="d-flex justify-content-between mt-2 text-muted small">
                        <span>Inexistant</span>
                        <span>Faible</span>
                        <span>Moyen</span>
                        <span>Bon</span>
                        <span>Très bon</span>
                        <span>Excellent</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    initializeSliders() {
        const sliders = document.querySelectorAll('.slider');
        
        sliders.forEach(sliderElement => {
            const indicateurId = sliderElement.dataset.indicateurId;
            
            noUiSlider.create(sliderElement, {
                start: [0],
                connect: [true, false],
                range: {
                    'min': 0,
                    'max': 5
                },
                step: 1,
                tooltips: true,
                format: {
                    to: (value) => {
                        const labels = ['Non observé', 'Émergent', 'En cours', 'Acquis', 'Maîtrisé', 'Expert'];
                        return labels[Math.round(value)] || Math.round(value);
                    },
                    from: (value) => Number(value)
                }
            });
            
            // Animations
            sliderElement.addEventListener('mouseenter', () => {
                sliderElement.style.transform = 'scale(1.02)';
            });
            
            sliderElement.addEventListener('mouseleave', () => {
                sliderElement.style.transform = 'scale(1)';
            });
            
            // Écouter les changements
            sliderElement.noUiSlider.on('update', (values) => {
                this.onSliderChange(sliderElement, values[0], indicateurId);
            });
        });
    }
    
    onSliderChange(sliderElement, value, indicateurId) {
        const numValue = parseInt(value);
        const domaineId = sliderElement.dataset.domaineId;
        
        // Mettre à jour l'affichage de la valeur
        const valueDisplay = document.getElementById(`value-${indicateurId}`);
        valueDisplay.textContent = numValue;
        
        // Animation de la valeur
        valueDisplay.classList.add('animate__animated', 'animate__pulse');
        setTimeout(() => {
            valueDisplay.classList.remove('animate__animated', 'animate__pulse');
        }, 600);
        
        // Sauvegarder le score
        if (!this.currentScores[domaineId]) {
            this.currentScores[domaineId] = {};
        }
        
        const oldValue = this.currentScores[domaineId][indicateurId]?.value || 0;
        this.currentScores[domaineId][indicateurId] = {
            value: numValue,
            poids: parseFloat(sliderElement.dataset.poids)
        };
        
        // Tracking des indicateurs cotés
        if (oldValue === 0 && numValue > 0) {
            this.indicateursCotes++;
        } else if (oldValue > 0 && numValue === 0) {
            this.indicateursCotes--;
        }
        
        // Recalculer les scores
        this.updateScores();
        this.updateProgressDisplay();
        this.updateSaveButtonState();
        
        // Feedback tactile (si supporté)
        if ('vibrate' in navigator) {
            navigator.vibrate(10);
        }
    }
    
    updateScores() {
        let totalScore = 0;
        let totalWeight = 0;
        const scoresDetail = document.getElementById('scores-summary');
        scoresDetail.innerHTML = '';
        
        // Calculer les scores par domaine
        Object.keys(this.currentScores).forEach(domaineId => {
            const domaineScores = this.currentScores[domaineId];
            let domaineTotal = 0;
            let domaineWeight = 0;
            
            Object.values(domaineScores).forEach(score => {
                domaineTotal += score.value * score.poids;
                domaineWeight += score.poids * 5; // 5 = score maximum
            });
            
            const domainePercent = domaineWeight > 0 ? Math.round((domaineTotal / domaineWeight) * 100) : 0;
            
            // Mettre à jour l'affichage du domaine
            this.updateDomaineScore(domaineId, domainePercent);
            
            // Ajouter au total
            totalScore += domaineTotal;
            totalWeight += domaineWeight;
            
            // Ajouter au résumé
            this.addToScoresSummary(domaineId, domainePercent, scoresDetail);
        });
        
        // Score global
        const globalPercent = totalWeight > 0 ? Math.round((totalScore / totalWeight) * 100) : 0;
        this.updateGlobalScore(globalPercent);
    }
    
    updateDomaineScore(domaineId, percent) {
        const scoreDomaine = document.getElementById(`score-domaine-${domaineId}`);
        if (!scoreDomaine) return;
        
        scoreDomaine.textContent = `${percent}%`;
        
        // Couleur dynamique avec animation
        let backgroundColor, textColor;
        if (percent >= 80) {
            backgroundColor = 'rgba(34, 197, 94, 0.2)';
            textColor = '#15803d';
        } else if (percent >= 60) {
            backgroundColor = 'rgba(251, 191, 36, 0.2)';
            textColor = '#d97706';
        } else {
            backgroundColor = 'rgba(239, 68, 68, 0.2)';
            textColor = '#dc2626';
        }
        
        scoreDomaine.style.transition = 'all 0.3s ease';
        scoreDomaine.style.background = backgroundColor;
        scoreDomaine.style.color = textColor;
    }
    
    addToScoresSummary(domaineId, percent, container) {
        const domaineElement = document.querySelector(`[data-domaine-id="${domaineId}"]`);
        if (!domaineElement) return;
        
        const domaineNom = domaineElement.closest('.domaine-section')
            .querySelector('.domaine-title').textContent.trim()
            .replace(/^\s*\S+\s*/, '');
        
        container.innerHTML += `
            <div class="score-item animate__animated animate__fadeInUp">
                <span class="flex-grow-1">${this.sanitizeHtml(domaineNom)}</span>
                <div class="d-flex align-items-center">
                    <div class="progress me-2" style="width: 60px; height: 6px;">
                        <div class="progress-bar bg-primary" style="width: ${percent}%"></div>
                    </div>
                    <span class="small fw-semibold text-primary">${percent}%</span>
                </div>
            </div>
        `;
    }
    
    updateGlobalScore(percent) {
        const scoreDisplay = document.getElementById('score-display');
        const scoreValue = scoreDisplay.querySelector('.score-value');
        
        // Animation du score
        const currentValue = parseInt(scoreValue.textContent) || 0;
        this.animateCounter(scoreValue, currentValue, percent, 50);
        
        // Couleur dynamique du cercle
        let backgroundColor, borderColor;
        if (percent >= 80) {
            backgroundColor = 'rgba(34, 197, 94, 0.2)';
            borderColor = 'rgba(34, 197, 94, 0.5)';
        } else if (percent >= 60) {
            backgroundColor = 'rgba(251, 191, 36, 0.2)';
            borderColor = 'rgba(251, 191, 36, 0.5)';
        } else {
            backgroundColor = 'rgba(239, 68, 68, 0.2)';
            borderColor = 'rgba(239, 68, 68, 0.5)';
        }
        
        scoreDisplay.style.transition = 'all 0.3s ease';
        scoreDisplay.style.background = backgroundColor;
        scoreDisplay.style.borderColor = borderColor;
    }
    
    animateCounter(element, start, end, duration) {
        const range = end - start;
        const stepTime = Math.abs(Math.floor(duration / range));
        const timer = setInterval(() => {
            start += start < end ? 1 : -1;
            element.textContent = start;
            if (start === end) {
                clearInterval(timer);
            }
        }, stepTime);
    }
    
    updateProgressDisplay() {
        const progressBar = document.getElementById('cotation-progress-bar');
        const progressText = document.getElementById('progress-text');
        
        if (!progressBar || !progressText) return;
        
        const progressPercent = this.totalIndicateurs > 0 ? 
            (this.indicateursCotes / this.totalIndicateurs) * 100 : 0;
        
        progressBar.style.width = `${progressPercent}%`;
        progressText.textContent = `${this.indicateursCotes} / ${this.totalIndicateurs} indicateurs cotés`;
        
        // Animation de la barre
        if (progressPercent === 100) {
            progressBar.classList.add('animate__animated', 'animate__pulse');
        }
    }
    
    updateSaveButtonState() {
        const btnSave = document.getElementById('btn-save');
        if (!btnSave) return;
        
        const hasScores = Object.keys(this.currentScores).length > 0 && this.indicateursCotes > 0;
        const observations = document.getElementById('observations')?.value.trim();
        
        btnSave.disabled = !hasScores;
        
        if (hasScores) {
            btnSave.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                btnSave.classList.remove('animate__animated', 'animate__pulse');
            }, 1000);
        }
    }
    
    setupProgressTracking() {
        setTimeout(() => {
            const progressElement = document.querySelector('.cotation-progress');
            if (progressElement) {
                progressElement.classList.add('animate__animated', 'animate__fadeInRight');
            }
        }, 500);
    }
    
    previewResults() {
        const modal = new bootstrap.Modal(document.getElementById('previewModal'));
        const content = document.getElementById('preview-content');
        
        if (!content) return;
        
        const globalScore = document.getElementById('score-display').querySelector('.score-value').textContent;
        const observations = document.getElementById('observations').value;
        
        let previewHTML = `
            <div class="mb-4">
                <h6 class="text-primary">Résumé de la cotation</h6>
                <div class="row">
                    <div class="col-md-8">
                        <p><strong>Patient:</strong> ${this.getPatientInfo()}</p>
                        <p><strong>Date:</strong> ${this.getSeanceDate()}</p>
                        <p><strong>Grille utilisée:</strong> ${this.getGrilleNom()}</p>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="score-circle-large mx-auto">
                            <span class="score-value">${globalScore}</span>
                            <span class="score-unit">%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mb-4">
                <h6 class="text-primary">Scores par domaine</h6>
                <div id="preview-domaines">${document.getElementById('scores-summary').innerHTML}</div>
            </div>
            
            <div class="mb-4">
                <h6 class="text-primary">Observations</h6>
                <div class="border rounded p-3 bg-light">
                    ${observations || '<em class="text-muted">Aucune observation saisie</em>'}
                </div>
            </div>
        `;
        
        content.innerHTML = previewHTML;
        modal.show();
    }
    
    async saveCotation() {
        const observations = document.getElementById('observations')?.value || '';
        
        if (Object.keys(this.currentScores).length === 0) {
            this.showAlert('Veuillez évaluer au moins un indicateur avant d\'enregistrer.', 'warning');
            return;
        }
        
        const btnSave = document.getElementById('btn-save');
        const originalText = btnSave.innerHTML;
        
        // État de chargement
        btnSave.disabled = true;
        btnSave.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Enregistrement...';
        this.showLoading(true);
        
        const cotationData = {
            seance_id: this.seanceId,
            grille_id: this.currentGrilleId,
            scores: this.currentScores,
            observations: observations
        };
        
        try {
            const response = await fetch('/cotation/api/cotation/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(cotationData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('Cotation enregistrée avec succès !', 'success');
                
                // Animation de succès
                btnSave.innerHTML = '<i class="bi bi-check-lg me-2"></i>Enregistré !';
                btnSave.classList.add('btn-success');
                btnSave.classList.remove('btn-primary');
                
                setTimeout(() => {
                    this.redirectToPatient();
                }, 2000);
            } else {
                throw new Error(data.message || 'Erreur lors de l\'enregistrement');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showAlert('Erreur lors de l\'enregistrement de la cotation: ' + error.message, 'error');
            
            // Restaurer le bouton
            btnSave.disabled = false;
            btnSave.innerHTML = originalText;
        } finally {
            this.showLoading(false);
        }
    }
    
    resetCotation() {
        if (confirm('Êtes-vous sûr de vouloir réinitialiser toute la cotation ?')) {
            this.currentScores = {};
            this.indicateursCotes = 0;
            
            // Réinitialiser tous les sliders
            document.querySelectorAll('.slider').forEach(slider => {
                if (slider.noUiSlider) {
                    slider.noUiSlider.set(0);
                }
            });
            
            // Réinitialiser les observations
            const observations = document.getElementById('observations');
            if (observations) {
                observations.value = '';
            }
            
            // Réinitialiser les affichages
            this.updateProgressDisplay();
            this.updateGlobalScore(0);
            this.updateSaveButtonState();
            
            this.showAlert('Cotation réinitialisée', 'info');
        }
    }
    
    handleKeyboardShortcuts(event) {
        // Ctrl+S pour sauvegarder
        if (event.ctrlKey && event.key === 's') {
            event.preventDefault();
            this.saveCotation();
        }
        
        // Ctrl+R pour réinitialiser
        if (event.ctrlKey && event.key === 'r') {
            event.preventDefault();
            this.resetCotation();
        }
        
        // Échap pour fermer les modals
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    }
    
    setupAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                }
            });
        });
        
        document.querySelectorAll('.card').forEach(card => {
            observer.observe(card);
        });
    }
    
    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show animate__animated animate__fadeInDown`;
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
        `;
        
        const iconMap = {
            success: 'check-circle-fill',
            warning: 'exclamation-triangle-fill',
            error: 'x-circle-fill',
            info: 'info-circle-fill'
        };
        
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-${iconMap[type] || iconMap.info} me-2"></i>
                ${this.sanitizeHtml(message)}
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-hide après 5 secondes
        setTimeout(() => {
            alertDiv.classList.add('animate__fadeOutUp');
            setTimeout(() => alertDiv.remove(), 500);
        }, 5000);
    }
    
    showFeedback(message, type, duration = 3000) {
        const feedback = document.createElement('div');
        feedback.className = `toast align-items-center text-white bg-${type} border-0 animate__animated animate__fadeInRight`;
        feedback.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
        `;
        
        feedback.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${this.sanitizeHtml(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.body.appendChild(feedback);
        
        const toast = new bootstrap.Toast(feedback, { delay: duration });
        toast.show();
        
        feedback.addEventListener('hidden.bs.toast', () => {
            feedback.remove();
        });
    }
    
    showLoading(show) {
        const container = document.querySelector('.container-fluid');
        if (show) {
            container.classList.add('loading');
        } else {
            container.classList.remove('loading');
        }
    }
    
    // Utility methods
    sanitizeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    getCsrfToken() {
        const csrfToken = document.querySelector('meta[name=csrf-token]');
        return csrfToken ? csrfToken.getAttribute('content') : '';
    }
    
    getPatientInfo() {
        // À adapter selon la structure du template
        const breadcrumb = document.querySelector('.breadcrumb-item:nth-child(2) a');
        return breadcrumb ? breadcrumb.textContent : 'Patient';
    }
    
    getSeanceDate() {
        // À adapter selon la structure du template
        const dateElement = document.querySelector('[class*="bi-calendar3"]');
        return dateElement ? dateElement.parentElement.textContent.trim() : 'Date inconnue';
    }
    
    getGrilleNom() {
        const selectedGrille = document.querySelector('.grille-radio:checked');
        if (selectedGrille) {
            const label = selectedGrille.closest('.grille-card').querySelector('.card-title');
            return label ? label.textContent : 'Grille sélectionnée';
        }
        return 'Aucune grille';
    }
    
    redirectToPatient() {
        // Récupérer l'URL du patient depuis le breadcrumb
        const patientLink = document.querySelector('.breadcrumb-item:nth-child(2) a');
        if (patientLink) {
            window.location.href = patientLink.href;
        } else {
            window.location.href = '/dashboard';
        }
    }
}

// Fonctions globales pour compatibilité
function previewResults() {
    if (window.cotationInterface) {
        window.cotationInterface.previewResults();
    }
}

function resetCotation() {
    if (window.cotationInterface) {
        window.cotationInterface.resetCotation();
    }
}

function saveCotation() {
    if (window.cotationInterface) {
        window.cotationInterface.saveCotation();
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    window.cotationInterface = new CotationInterface();
});
