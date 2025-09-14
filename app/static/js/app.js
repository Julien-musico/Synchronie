// JavaScript principal pour Synchronie

// Utilitaires globaux
class SynchronieApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initTooltips();
        this.initAnimations();
        console.log('🎵 Synchronie App initialized');
    }

    setupEventListeners() {
        // Gestionnaire global pour les boutons avec loading
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-loading')) {
                this.showButtonLoading(e.target);
            }
        });

        // Gestionnaire pour les formulaires avec validation
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('form-validate')) {
                this.validateForm(e);
            }
        });
    }

    initTooltips() {
        // Initialiser les tooltips Bootstrap
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initAnimations() {
        // Observer pour les animations au scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);

        // Observer tous les éléments avec la classe animate-on-scroll
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    showButtonLoading(button) {
        const originalText = button.innerHTML;
        const loadingText = button.dataset.loading || 'Chargement...';
        
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${loadingText}
        `;
        button.disabled = true;

        // Restaurer le bouton après 3 secondes (ou quand l'action est terminée)
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }

    validateForm(event) {
        const form = event.target;
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'Ce champ est obligatoire');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });

        if (!isValid) {
            event.preventDefault();
            this.showAlert('Veuillez remplir tous les champs obligatoires', 'danger');
        }
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    showAlert(message, type = 'info', duration = 5000) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="bi bi-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const container = document.querySelector('.container');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
            
            // Auto-dismiss après la durée spécifiée
            setTimeout(() => {
                const alert = container.querySelector('.alert');
                if (alert) {
                    alert.remove();
                }
            }, duration);
        }
    }

    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'exclamation-triangle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Utilitaires pour les API calls
    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Erreur de l\'API');
            }

            return data;
        } catch (error) {
            console.error('Erreur API:', error);
            this.showAlert(`Erreur: ${error.message}`, 'danger');
            throw error;
        }
    }

    // Utilitaires pour le formatage
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('fr-FR');
    }

    formatDuration(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        
        if (hours > 0) {
            return `${hours}h${mins.toString().padStart(2, '0')}`;
        }
        return `${mins}min`;
    }

    // Utilitaires pour le stockage local
    saveToStorage(key, data) {
        try {
            localStorage.setItem(`synchronie_${key}`, JSON.stringify(data));
        } catch (error) {
            console.warn('Impossible de sauvegarder en local:', error);
        }
    }

    loadFromStorage(key) {
        try {
            const data = localStorage.getItem(`synchronie_${key}`);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.warn('Impossible de charger depuis le local:', error);
            return null;
        }
    }
}

// Utilitaires spécifiques aux patients
class PatientManager {
    constructor(app) {
        this.app = app;
    }

    async searchPatients(query) {
        return await this.app.apiCall(`/api/patients/search?q=${encodeURIComponent(query)}`);
    }

    async getPatient(patientId) {
        return await this.app.apiCall(`/api/patients/${patientId}`);
    }

    async createPatient(patientData) {
        return await this.app.apiCall('/api/patients', {
            method: 'POST',
            body: JSON.stringify(patientData)
        });
    }

    async updatePatient(patientId, patientData) {
        return await this.app.apiCall(`/api/patients/${patientId}`, {
            method: 'PUT',
            body: JSON.stringify(patientData)
        });
    }
}

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', function() {
    // Créer l'instance principale de l'app
    window.synchronieApp = new SynchronieApp();
    window.patientManager = new PatientManager(window.synchronieApp);

    // Ajouter des animations aux éléments existants
    document.querySelectorAll('.card, .alert').forEach(el => {
        el.classList.add('animate-on-scroll');
    });

    // Activer les tooltips pour tous les éléments avec title
    document.querySelectorAll('[title]').forEach(el => {
        el.setAttribute('data-bs-toggle', 'tooltip');
    });

    // Re-initialiser les tooltips
    window.synchronieApp.initTooltips();

    // Génération de rapport patient
    const formRapport = document.getElementById('form-rapport');
    if (formRapport) {
        formRapport.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-launch-rapport');
            const spinner = btn.querySelector('.spinner-border');
            const label = btn.querySelector('.label');
            spinner.classList.remove('d-none');
            label.textContent = 'Génération...';
            btn.disabled = true;
            const patientId = document.getElementById('btn-generate-report').dataset.patientId;
            const fd = new FormData(formRapport);
            const payload = {
                date_debut: fd.get('date_debut'),
                date_fin: fd.get('date_fin'),
                periodicite: fd.get('periodicite') || null
            };
            try {
                const res = await fetch(`/api/patients/${patientId}/rapport`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!data.success) {
                    window.synchronieApp.showAlert(data.message || 'Erreur génération', 'danger');
                } else {
                    const rapportZone = document.getElementById('rapport-result');
                    const contenu = document.getElementById('rapport-contenu');
                    contenu.textContent = data.rapport || '(Vide)';
                    rapportZone.classList.remove('d-none');
                    window.synchronieApp.showAlert('Rapport généré', 'success');
                    // Insertion dans la liste des rapports (mémoire volatile côté client)
                    const container = document.getElementById('rapports-patient');
                    const list = document.getElementById('rapports-list');
                    if (container && list) {
                        container.classList.remove('d-none');
                        const item = document.createElement('div');
                        item.className = 'list-group-item';
                        item.innerHTML = `
                          <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">Rapport du ${new Date(data.date_generation).toLocaleDateString('fr-FR')}</h6>
                            <small class="text-muted">Période: ${data.date_debut} → ${data.date_fin}</small>
                          </div>
                          <div class="mt-2" style="white-space: pre-wrap;">${(data.rapport || '').replace(/</g,'&lt;')}</div>`;
                        list.prepend(item);
                    }
                }
            } catch (err) {
                window.synchronieApp.showAlert('Erreur réseau lors de la génération', 'danger');
            } finally {
                spinner.classList.add('d-none');
                label.textContent = 'Générer';
                btn.disabled = false;
            }
        });
    }
});

// Export des fonctions utilitaires pour utilisation globale
window.SynchronieUtils = {
    formatDate: (date) => window.synchronieApp.formatDate(date),
    formatDateTime: (date) => window.synchronieApp.formatDateTime(date),
    formatDuration: (minutes) => window.synchronieApp.formatDuration(minutes),
    showAlert: (message, type, duration) => window.synchronieApp.showAlert(message, type, duration),
    apiCall: (url, options) => window.synchronieApp.apiCall(url, options)
};
