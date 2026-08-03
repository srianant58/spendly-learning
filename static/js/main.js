// main.js — students will add JavaScript here as features are built

(function () {
    var trigger = document.getElementById('how-it-works-btn');
    var overlay = document.getElementById('how-it-works-modal');
    var closeBtn = document.getElementById('how-it-works-close');
    var iframe = document.getElementById('how-it-works-iframe');

    if (!trigger || !overlay || !closeBtn || !iframe) return;

    function openModal() {
        iframe.src = iframe.dataset.src + '?autoplay=1';
        overlay.hidden = false;
    }

    function closeModal() {
        overlay.hidden = true;
        iframe.src = '';
    }

    trigger.addEventListener('click', function (e) {
        e.preventDefault();
        openModal();
    });

    closeBtn.addEventListener('click', closeModal);

    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !overlay.hidden) closeModal();
    });
})();
