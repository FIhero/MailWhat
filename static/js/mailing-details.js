let currentAttemptData = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Mailing details JS loaded');
    
    initModal();
    
    initDetailButtons();
});

function initModal() {
    const detailsModal = document.getElementById('details-modal');
    const modalClose = document.querySelector('#details-modal .modal-close');
    const modalCancel = document.querySelector('#details-modal .btn-cancel');
    
    if (modalClose) {
        modalClose.addEventListener('click', closeDetailsModal);
    }
    
    if (modalCancel) {
        modalCancel.addEventListener('click', closeDetailsModal);
    }
    
    if (detailsModal) {
        window.addEventListener('click', function(event) {
            if (event.target === detailsModal) {
                closeDetailsModal();
            }
        });
    }
    
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeDetailsModal();
        }
    });
}

function initDetailButtons() {
    const detailButtons = document.querySelectorAll('[onclick*="showMailingDetails"], [data-attempt-id]');
    
    console.log('Found detail buttons:', detailButtons.length);
    
    detailButtons.forEach(button => {
        if (!button.getAttribute('onclick')) {
            button.addEventListener('click', function() {
                const attemptId = this.getAttribute('data-attempt-id');
                if (attemptId) {
                    showMailingDetails(attemptId);
                }
            });
        }
    });
}

function showDetailsModal() {
    const detailsModal = document.getElementById('details-modal');
    if (detailsModal) {
        detailsModal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeDetailsModal() {
    const detailsModal = document.getElementById('details-modal');
    if (detailsModal) {
        detailsModal.style.display = 'none';
        document.body.style.overflow = '';
        currentAttemptData = null;
    }
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    const activeButton = document.querySelector(`.tab-button[onclick="switchTab('${tabName}')"]`);
    const activeContent = document.getElementById(`${tabName}-tab`);
    
    if (activeButton && activeContent) {
        activeButton.classList.add('active');
        activeContent.classList.add('active');
        loadTabData(tabName);
    }
}

function loadTabData(tabName) {
    if (!currentAttemptData) return;
    
    const container = document.getElementById(`${tabName}-tab`);
    if (!container) return;
    
    let recipients = [];
    
    switch(tabName) {
        case 'errors':
            recipients = currentAttemptData.recipients.filter(r => r.status === 'failure');
            break;
        case 'success':
            recipients = currentAttemptData.recipients.filter(r => r.status === 'success');
            break;
        case 'all':
            recipients = currentAttemptData.recipients;
            break;
    }
    
    container.innerHTML = '';
    
    if (recipients.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--primary-active);">Нет данных для отображения</div>';
        return;
    }
    
    recipients.forEach(recipient => {
        const isError = recipient.status === 'failure';
        const card = document.createElement('div');
        card.className = `recipient-card ${isError ? 'recipient-error' : 'recipient-success'}`;
        
        card.innerHTML = `
            <div class="recipient-info">
                <div class="recipient-email">${recipient.email}</div>
                ${recipient.full_name ? `<div class="recipient-name">${recipient.full_name}</div>` : ''}
                ${isError ? `<div class="error-message">${recipient.message}</div>` : ''}
            </div>
            <span class="recipient-status ${isError ? 'status-error' : 'status-success'}">
                ${isError ? 'Ошибка' : 'Успешно'}
            </span>
        `;
        container.appendChild(card);
    });
}

function showMailingDetails(attemptId) {
    console.log('Showing details for attempt:', attemptId);
    
    showDetailsModal();
    setLoadingState();
    
    fetch(`/attempts/${attemptId}/details/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data);
            currentAttemptData = data;
            updateModalContent(data);
            loadTabData('errors');
        })
        .catch(error => {
            console.error('Ошибка загрузки деталей:', error);
            setErrorState(error);
        });
}

function setLoadingState() {
    const elements = [
        'total-recipients', 'success-recipients', 'failed-recipients',
        'errors-count', 'success-count', 'mailing-subject',
        'mailing-time', 'mailing-status', 'mailing-body'
    ];
    
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.textContent = '...';
    });
}

function updateModalContent(data) {
    const total = data.recipients ? data.recipients.length : 0;
    const success = data.recipients ? data.recipients.filter(r => r.status === 'success').length : 0;
    const failure = data.recipients ? data.recipients.filter(r => r.status === 'failure').length : 0;
    
    document.getElementById('total-recipients').textContent = total;
    document.getElementById('success-recipients').textContent = success;
    document.getElementById('failed-recipients').textContent = failure;
    document.getElementById('errors-count').textContent = failure;
    document.getElementById('success-count').textContent = success;
    
    document.getElementById('mailing-subject').textContent = data.mailing_subject || 'Без темы';
    document.getElementById('mailing-time').textContent = data.created_at || 'Не указано';
    document.getElementById('mailing-status').textContent = data.status === 'success' ? '✅ Успешно' : '❌ Ошибка';
    document.getElementById('mailing-body').textContent = data.mailing_body || 'Текст сообщения не указан';
}

function setErrorState(error) {
    const subjectElement = document.getElementById('mailing-subject');
    const bodyElement = document.getElementById('mailing-body');
    
    if (subjectElement) subjectElement.textContent = 'Ошибка загрузки';
    if (bodyElement) bodyElement.textContent = 'Не удалось загрузить данные: ' + error.message;
}

function exportDetails() {
    if (!currentAttemptData) {
        alert('Нет данных для экспорта');
        return;
    }
    alert('Экспорт деталей в разработке! Данные готовы для экспорта.');
}

window.showMailingDetails = showMailingDetails;
window.switchTab = switchTab;
window.closeDetailsModal = closeDetailsModal;
window.exportDetails = exportDetails;