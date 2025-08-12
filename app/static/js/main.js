// Synchronie - Scripts JavaScript

$(document).ready(function() {
    // Initialisation des tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialisation des popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss des alertes après 5 secondes
    $('.alert:not(.alert-permanent)').delay(5000).fadeOut(350);

    // Confirmation de suppression
    $('.delete-confirm').on('click', function(e) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
            e.preventDefault();
        }
    });

    // Upload de fichiers avec drag & drop
    initFileUpload();

    // Recherche en temps réel
    initLiveSearch();

    // Formulaires de cotation
    initRatingForms();
});

// Gestion de l'upload de fichiers
function initFileUpload() {
    $('.upload-zone').on({
        'dragover': function(e) {
            e.preventDefault();
            $(this).addClass('dragover');
        },
        'dragleave': function(e) {
            e.preventDefault();
            $(this).removeClass('dragover');
        },
        'drop': function(e) {
            e.preventDefault();
            $(this).removeClass('dragover');
            
            var files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0], $(this));
            }
        },
        'click': function() {
            $(this).find('input[type="file"]').click();
        }
    });

    $('input[type="file"]').on('change', function() {
        var file = this.files[0];
        if (file) {
            handleFileUpload(file, $(this).closest('.upload-zone'));
        }
    });
}

function handleFileUpload(file, uploadZone) {
    // Vérification du type de fichier
    var allowedTypes = ['audio/mp3', 'audio/wav', 'audio/flac', 'audio/m4a', 'audio/ogg', 'audio/aac'];
    if (!allowedTypes.includes(file.type)) {
        showAlert('Type de fichier non supporté. Formats acceptés : MP3, WAV, FLAC, M4A, OGG, AAC', 'error');
        return;
    }

    // Vérification de la taille (100MB max)
    if (file.size > 100 * 1024 * 1024) {
        showAlert('Fichier trop volumineux. Taille maximum : 100MB', 'error');
        return;
    }

    // Mise à jour de l'interface
    uploadZone.html(`
        <div class="upload-progress">
            <i class="fas fa-file-audio fa-2x text-primary mb-2"></i>
            <p class="mb-2">${file.name}</p>
            <div class="progress">
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            </div>
            <small class="text-muted">Upload en cours...</small>
        </div>
    `);

    // Simulation de l'upload (à remplacer par une vraie implementation)
    simulateUpload(uploadZone);
}

function simulateUpload(uploadZone) {
    var progress = 0;
    var interval = setInterval(function() {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            uploadZone.find('.progress-bar').css('width', '100%');
            uploadZone.find('small').text('Upload terminé !').removeClass('text-muted').addClass('text-success');
            
            // Redirection ou mise à jour de la page
            setTimeout(function() {
                location.reload();
            }, 1000);
        } else {
            uploadZone.find('.progress-bar').css('width', progress + '%');
        }
    }, 200);
}

// Recherche en temps réel
function initLiveSearch() {
    var searchInput = $('#live-search');
    var searchTimeout;

    searchInput.on('input', function() {
        clearTimeout(searchTimeout);
        var query = $(this).val();

        if (query.length >= 2) {
            searchTimeout = setTimeout(function() {
                performSearch(query);
            }, 300);
        } else if (query.length === 0) {
            clearSearchResults();
        }
    });
}

function performSearch(query) {
    $.ajax({
        url: '/patients/search-api',
        data: { q: query },
        success: function(results) {
            displaySearchResults(results);
        },
        error: function() {
            showAlert('Erreur lors de la recherche', 'error');
        }
    });
}

function displaySearchResults(results) {
    var resultsContainer = $('#search-results');
    if (results.length === 0) {
        resultsContainer.html('<div class="alert alert-info">Aucun résultat trouvé</div>');
        return;
    }

    var html = '<div class="list-group">';
    results.forEach(function(result) {
        html += `
            <a href="/patients/${result.id}" class="list-group-item list-group-item-action">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${result.name}</h6>
                        <small class="text-muted">${result.age} ans</small>
                    </div>
                    <span class="badge bg-${getStatusColor(result.status)}">${result.status}</span>
                </div>
            </a>
        `;
    });
    html += '</div>';
    
    resultsContainer.html(html);
}

function clearSearchResults() {
    $('#search-results').empty();
}

function getStatusColor(status) {
    const colors = {
        'active': 'success',
        'paused': 'warning',
        'completed': 'info',
        'discontinued': 'danger'
    };
    return colors[status] || 'secondary';
}

// Formulaires de cotation
function initRatingForms() {
    $('.rating-scale').each(function() {
        var scale = $(this);
        var input = scale.find('input[type="hidden"]');
        var buttons = scale.find('.rating-btn');

        buttons.on('click', function() {
            var value = $(this).data('value');
            input.val(value);
            
            buttons.removeClass('active');
            $(this).addClass('active');
            
            // Mettre à jour l'affichage visuel
            updateRatingDisplay(scale, value);
        });
    });
}

function updateRatingDisplay(scale, value) {
    var maxValue = scale.data('max') || 5;
    var percentage = (value / maxValue) * 100;
    
    scale.find('.rating-visual').css('width', percentage + '%');
    scale.find('.rating-value').text(value + '/' + maxValue);
}

// Fonctions utilitaires
function showAlert(message, type) {
    var alertClass = 'alert-info';
    switch(type) {
        case 'success': alertClass = 'alert-success'; break;
        case 'error': alertClass = 'alert-danger'; break;
        case 'warning': alertClass = 'alert-warning'; break;
    }

    var alert = $(`
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);

    $('.container').first().prepend(alert);
    
    // Auto-dismiss après 5 secondes
    setTimeout(function() {
        alert.fadeOut(350, function() {
            $(this).remove();
        });
    }, 5000);
}

function formatDuration(seconds) {
    var hours = Math.floor(seconds / 3600);
    var minutes = Math.floor((seconds % 3600) / 60);
    var secs = seconds % 60;

    if (hours > 0) {
        return `${hours}h${minutes.toString().padStart(2, '0')}min`;
    } else {
        return `${minutes}min${secs.toString().padStart(2, '0')}s`;
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    var k = 1024;
    var sizes = ['Bytes', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Fonctions pour les graphiques (Chart.js sera ajouté plus tard)
function createProgressChart(containerId, data) {
    // TODO: Implémenter avec Chart.js
    console.log('Creating progress chart for', containerId, data);
}

function createEngagementChart(containerId, data) {
    // TODO: Implémenter avec Chart.js
    console.log('Creating engagement chart for', containerId, data);
}
