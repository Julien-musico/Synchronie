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
                if (!data.success || !data.data) {
                    window.synchronieApp.showAlert(data.message || 'Erreur génération', 'danger');
                } else {
                    const rapportDict = data.data;
                    const rapportZone = document.getElementById('rapport-result');
                    const contenu = document.getElementById('rapport-contenu');
                    contenu.textContent = (rapportDict.contenu || rapportDict.rapport || '').trim() || '(Vide)';
                    rapportZone.classList.remove('d-none');
                    window.synchronieApp.showAlert('Rapport généré', 'success');
                    ajouterRapportAListe(rapportDict, true);
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

    // Chargement initial des rapports si la section existe
    const rapportsList = document.getElementById('rapports-list');
    const patientGenerateBtn = document.getElementById('btn-generate-report');
    if (rapportsList && patientGenerateBtn) {
        const patientId = patientGenerateBtn.dataset.patientId;
        chargerRapports(patientId);
    }

    // Délégation pour actions sur les rapports (toggle & delete)
    document.addEventListener('click', async (e) => {
        const toggleBtn = e.target.closest('[data-action="toggle-rapport"]');
        if (toggleBtn) {
            const targetId = toggleBtn.getAttribute('data-target');
            const body = document.getElementById(targetId);
            if (body) {
                body.classList.toggle('d-none');
                const icon = toggleBtn.querySelector('i');
                if (icon) {
                    icon.classList.toggle('bi-chevron-down');
                    icon.classList.toggle('bi-chevron-up');
                }
            }
        }

        const deleteBtn = e.target.closest('[data-action="delete-rapport"]');
        if (deleteBtn) {
            const rapportId = deleteBtn.getAttribute('data-id');
            if (!rapportId) return;
            if (!confirm('Supprimer définitivement ce rapport ?')) return;
            try {
                const resp = await fetch(`/api/rapports/${rapportId}`, { method: 'DELETE' });
                const json = await resp.json();
                if (json.success) {
                    const wrapper = document.getElementById(`rapport-wrapper-${rapportId}`);
                    if (wrapper) wrapper.remove();
                    verifierEtatListe();
                    window.synchronieApp.showAlert('Rapport supprimé', 'success');
                } else {
                    window.synchronieApp.showAlert(json.message || 'Erreur suppression', 'danger');
                }
            } catch (err) {
                window.synchronieApp.showAlert('Erreur réseau suppression', 'danger');
            }
        }
    });

    function creerItemRapport(r) {
        const id = r.id;
        const rapportDate = new Date(r.date_generation).toLocaleDateString('fr-FR');
        const periode = `${r.date_debut} → ${r.date_fin}`;
        const periodicite = r.periodicite ? `<span class="badge bg-info ms-2">${r.periodicite}</span>` : '';
        const wrapper = document.createElement('div');
        wrapper.id = `rapport-wrapper-${id}`;
        wrapper.className = 'list-group-item p-0 border-0';
        wrapper.innerHTML = `
            <div class="border rounded mb-2">
                <div class="d-flex align-items-center justify-content-between px-3 py-2 bg-light">
                    <div>
                        <button class="btn btn-sm btn-link text-decoration-none" data-action="toggle-rapport" data-target="rapport-body-${id}">
                            <i class="bi bi-chevron-down me-1"></i>
                            Rapport du ${rapportDate}
                        </button>
                        <small class="text-muted ms-2">Période: ${periode}</small>
                        ${periodicite}
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-danger" title="Supprimer" data-action="delete-rapport" data-id="${id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div id="rapport-body-${id}" class="px-3 py-3 d-none" style="white-space: pre-wrap;">
                    ${ (r.contenu || '').replace(/</g,'&lt;') }
                </div>
            </div>`;
        return wrapper;
    }

    function ajouterRapportAListe(r, prepend=false) {
        const container = document.getElementById('rapports-patient');
        const emptyState = document.getElementById('rapports-empty');
        if (container) container.classList.remove('d-none');
        if (emptyState) emptyState.classList.add('d-none');
        const list = document.getElementById('rapports-list');
        if (!list) return;
        const item = creerItemRapport(r);
        if (prepend) {
            list.prepend(item);
        } else {
            list.appendChild(item);
        }
    }

    async function chargerRapports(patientId) {
        try {
            const resp = await fetch(`/api/patients/${patientId}/rapports`);
            const json = await resp.json();
            if (json.success && Array.isArray(json.data) && json.data.length) {
                json.data.forEach(r => ajouterRapportAListe(r));
            } else {
                verifierEtatListe();
            }
        } catch (err) {
            verifierEtatListe();
        }
    }

    function verifierEtatListe() {
        const list = document.getElementById('rapports-list');
        const emptyState = document.getElementById('rapports-empty');
        const container = document.getElementById('rapports-patient');
        if (list && list.children.length === 0) {
            if (emptyState) emptyState.classList.remove('d-none');
            if (container) container.classList.add('d-none');
        }
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
