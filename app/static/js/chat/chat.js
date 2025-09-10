document.addEventListener('DOMContentLoaded', function () {
    const chatButton = document.getElementById('chatButton');
    const chatModal = document.getElementById('chatModal');
    const minimizeBtn = document.getElementById('minimizeChat');
    const closeBtn = document.getElementById('closeChat');
    const endChatBtn = document.getElementById('endChat');
    const messageInput = document.getElementById('messageInput');
    const sendMessageBtn = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');

    let currentChatId = null;
    let isLoading = false;
    let hasMore = true;
    let page = 1;
    let isInitialized = false;

    // Открытие чата
    chatButton?.addEventListener('click', async function () {
        chatModal.style.display = 'block';
        if (!isInitialized) {
            await initializeChat();
            isInitialized = true;
        }
        loadMessages(true);
    });

    // Сворачивание
    minimizeBtn?.addEventListener('click', function () {
        chatModal.classList.toggle('minimized');
    });

    // Закрытие модалки (не завершает чат)
    closeBtn?.addEventListener('click', function () {
        chatModal.style.display = 'none';
    });

    // Завершение чата
    endChatBtn?.addEventListener('click', async function () {
        if (!currentChatId) return;

        try {
            const response = await fetch(`/chats/close?chat_id=${currentChatId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                alert('Чат успешно завершён.');
                chatModal.style.display = 'none';
                currentChatId = null;
                isInitialized = false;
                chatMessages.innerHTML = '<div class="message-system">Чат завершён. Начните новый.</div>';
            } else {
                throw new Error('Ошибка завершения чата');
            }
        } catch (error) {
            alert('Не удалось завершить чат: ' + error.message);
        }
    });

    // Отправка сообщения
    sendMessageBtn?.addEventListener('click', sendMessage);
    messageInput?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    async function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        try {
            const response = await fetch(`/messages/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            if (response.ok) {
                messageInput.value = '';
                loadMessages(false); // Обновляем без сброса скролла
            } else {
                throw new Error('Ошибка отправки');
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    }

    // Инициализация чата (создание или получение активного)
    async function initializeChat() {
        try {
            // Проверяем активные чаты
            const chatsRes = await fetch('/chats/my');
            const chats = await chatsRes.json();

            let activeChat = chats.find(c => c.active);

            if (!activeChat) {
                // Создаём новый чат
                const createRes = await fetch('/chats/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic: "Общая поддержка" })
                });
                const created = await createRes.json();
                if (!createRes.ok) throw new Error(created.detail || 'Ошибка создания чата');

                // Получаем ID нового чата
                const newChatsRes = await fetch('/chats/my');
                const newChats = await newChatsRes.json();
                activeChat = newChats.find(c => c.active);
            }

            currentChatId = activeChat.id;
            setupInfiniteScroll();
        } catch (error) {
            chatMessages.innerHTML = `<div class="message-system">Ошибка инициализации чата: ${error.message}</div>`;
        }
    }

    // Подгрузка сообщений
    async function loadMessages(reset = false) {
        if (isLoading || !hasMore || !currentChatId) return;

        isLoading = true;
        if (reset) {
            page = 1;
            hasMore = true;
            chatMessages.innerHTML = '<div class="message-system">Загрузка...</div>';
        }

        try {
            const url = `/messages/by_chat/${currentChatId}?page=${page}&limit=15`;
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || 'Ошибка загрузки');

            if (reset) {
                chatMessages.innerHTML = '';
            }

            if (data.length === 0 && page === 1) {
                chatMessages.innerHTML = '<div class="message-system">Нет сообщений. Начните диалог!</div>';
                hasMore = false;
                isLoading = false;
                return;
            }

            data.forEach(msg => {
                const isUser = msg.sender_id == document.querySelector('meta[name="user-id"]')?.content;
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'message-user' : 'message-support'}`;

                if (!isUser) {
                    messageDiv.innerHTML = `
                        <div class="sender-name">Оператор: ${msg.sender_name || 'Поддержка'}</div>
                        <div>${msg.message}</div>
                        <div class="message-info">${formatDateTime(msg.created_at)}</div>
                    `;
                } else {
                    messageDiv.innerHTML = `
                        <div>${msg.message}</div>
                        <div class="message-info">${formatDateTime(msg.created_at)}</div>
                    `;
                }

                chatMessages.appendChild(messageDiv);
            });

            if (data.length < 15) {
                hasMore = false;
            } else {
                page++;
            }

            // Автопрокрутка вниз, если сбрасывали
            if (reset) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

        } catch (error) {
            if (reset) {
                chatMessages.innerHTML = `<div class="message-system">Ошибка: ${error.message}</div>`;
            }
        } finally {
            isLoading = false;
        }
    }

    // Бесконечная прокрутка вверх
    function setupInfiniteScroll() {
        chatMessages.addEventListener('scroll', async function () {
            if (chatMessages.scrollTop === 0 && hasMore && !isLoading) {
                const currentScrollHeight = chatMessages.scrollHeight;
                await loadMessages(false);
                // Сохраняем позицию после подгрузки
                chatMessages.scrollTop = chatMessages.scrollHeight - currentScrollHeight;
            }
        });
    }

    function formatDateTime(isoString) {
        const date = new Date(isoString);
        return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
});