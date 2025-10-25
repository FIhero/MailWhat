const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalMessage = document.getElementById('modal-message');
const modalConfirm = document.getElementById('modal-confirm');
const modalCancel = document.getElementById('modal-cancel');
const modalClose = document.querySelector('.modal-close');

let confirmCallback = null;

function showModal(title, message, callback) {
    if (modalTitle) modalTitle.textContent = title;
    if (modalMessage) modalMessage.textContent = message;
    confirmCallback = callback;
    if (modal) modal.style.display = 'block';
}

function closeModal() {
    if (modal) modal.style.display = 'none';
    confirmCallback = null;
}

if (modalClose) {
    modalClose.addEventListener('click', closeModal);
}

if (modalCancel) {
    modalCancel.addEventListener('click', closeModal);
}

if (modalConfirm) {
    modalConfirm.addEventListener('click', function() {
        if (confirmCallback) {
            confirmCallback();
        }
        closeModal();
    });
}

window.addEventListener('click', function(event) {
    if (event.target === modal) {
        closeModal();
    }
});

function confirmMailingSend(url) {
    showModal(
        'Отправка рассылки',
        'Вы уверены, что хотите отправить эту рассылку сейчас? Все выбранные клиенты получат письмо.',
        function() {
            window.location.href = url;
        }
    );
}

function confirmDelete(url, objectName) {
    showModal(
        'Подтверждение удаления',
        `Вы уверены, что хотите удалить "${objectName}"? Это действие нельзя отменить.`,
        function() {
            window.location.href = url;
        }
    );
}

