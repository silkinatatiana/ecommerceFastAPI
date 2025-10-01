document.addEventListener('DOMContentLoaded', function () {
    const loadMoreBtn = document.querySelector('#load-more-container button');
    if (!loadMoreBtn) return;

    loadMoreBtn.addEventListener('click', async function () {
        const url = this.getAttribute('hx-get');
        const targetId = this.getAttribute('hx-target');
        const swap = this.getAttribute('hx-swap');

        try {
            const response = await fetch(url, {
                headers: {
                    'HX-Request': 'true'
                }
            });
            const html = await response.text();

            const target = document.querySelector(targetId);
            if (swap === 'outerHTML') {
                target.outerHTML = html;
            } else {
                target.innerHTML = html;
            }
        } catch (err) {
            console.error('Ошибка загрузки:', err);
            alert('Не удалось загрузить больше чатов.');
        }
    });
});
