async function loadMoreChats(page) {
    const loadMoreBtn = document.querySelector('.js-load-more-container button');
    if (loadMoreBtn) {
        loadMoreBtn.disabled = true;
        loadMoreBtn.textContent = 'Загрузка...';
    }

    try {
        const response = await fetch(`/chats/load-more?page=${page}`, {
            method: 'GET',
            headers: {
                'Accept': 'text/html'
            },
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Ошибка загрузки');
        const html = await response.text();
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;

        const chatsList = document.getElementById('chatsList');
        const newChatItems = tempDiv.querySelectorAll('.chat-item');
        newChatItems.forEach(item => {
            chatsList.appendChild(item);
        });

        const newLoadMoreContainer = tempDiv.querySelector('.js-load-more-container');
        const currentLoadMoreContainer = document.querySelector('.js-load-more-container');
        if (newLoadMoreContainer && currentLoadMoreContainer) {
            currentLoadMoreContainer.innerHTML = newLoadMoreContainer.innerHTML;
        }

    } catch (error) {
        console.error('Ошибка:', error);
        if (loadMoreBtn) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.textContent = 'Загрузить ещё';
        }
        alert('Не удалось загрузить чаты');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const openChatBtn = document.getElementById('openChatBtn');
    const chatButton = document.getElementById('chatButton');

    if (openChatBtn && chatButton) {
        openChatBtn.addEventListener('click', function (e) {
            e.preventDefault();
            chatButton.click();
        });
    }
});