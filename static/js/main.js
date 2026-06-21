// main.js — students will add JavaScript here as features are built

(function () {
    var modal = document.getElementById('delete-modal');
    if (!modal) return;

    var cancelBtn  = document.getElementById('delete-modal-cancel');
    var closeBtn   = document.getElementById('delete-modal-close');
    var confirmBtn = document.getElementById('delete-modal-confirm');
    var pendingForm = null;

    function openModal(form) {
        pendingForm = form;
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        cancelBtn.focus();
    }

    function closeModal() {
        pendingForm = null;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
    }

    document.querySelectorAll('.delete-expense-form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            openModal(form);
        });
    });

    confirmBtn.addEventListener('click', function () {
        if (pendingForm) pendingForm.submit();
    });

    cancelBtn.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
    });
}());
