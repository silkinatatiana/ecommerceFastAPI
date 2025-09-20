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

    chatButton?.addEventListener('click', async function () {
        chatModal.style.display = 'block';
        if (!isInitialized) {
            await initializeChat();
            isInitialized = true;
        }
        loadMessages(true);
    });

    minimizeBtn?.addEventListener('click', function () {
        chatModal.classList.toggle('minimized');
    });

    closeBtn?.addEventListener('click', function () {
        chatModal.style.display = 'none';
    });

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

                updateEndChatButtonVisibility();

                chatMessages.innerHTML = '<div class="message-system">Чат завершён. Начните новый.</div>';
            } else {
                throw new Error('Ошибка завершения чата');
            }
        } catch (error) {
            alert('Не удалось завершить чат: ' + error.message);
        }
    });

    sendMessageBtn?.addEventListener('click', sendMessage);
    messageInput?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    async function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        try {
            let chatId = currentChatId;

            if (!chatId) {
                const createChatRes = await fetch('/chats/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        topic: getChatTopicByPage()
                    })
                });

                if (!createChatRes.ok) {
                    const errorData = await createChatRes.json();
                    throw new Error(errorData.detail || 'Не удалось создать чат');
                }

                const chatsRes = await fetch('/chats/my');
                const chats = await chatsRes.json();
                const activeChat = chats.find(c => c.active);

                if (!activeChat) {
                    throw new Error('Чат создан, но не найден в списке');
                }

                chatId = activeChat.id;
                currentChatId = chatId;
                updateEndChatButtonVisibility();

                const prompt = document.getElementById('initialPrompt');
                if (prompt) prompt.remove();

                setupInfiniteScroll();
                await loadMessages(true);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            const response = await fetch('/messages/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chat_id: chatId,
                    message: text
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка отправки');
            }

            messageInput.value = '';

            if (currentChatId === chatId) {
                const userId = document.querySelector('meta[name="user-id"]')?.content;
                const newMessage = {
                    id: Date.now(),
                    chat_id: chatId,
                    sender_id: userId,
                    sender_name: 'Вы',
                    message: text,
                    created_at: new Date().toISOString()
                };

                addMessageToChat(newMessage);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    }

    function getChatTopicByPage() {
        const path = window.location.pathname;

        if (path === '/') {
            return "Вопрос по каталогу товаров";
        } else if (path.startsWith('/products')) {
            return "Вопрос по товару";
        } else if (path.startsWith('/orders')) {
            return "Вопрос по заказу";
        } else if (path.startsWith('/auth')) {
            return "Вопрос по профилю";
        } else if (path === '/cart/') {
            return "Вопрос по корзине";
        } else {
            return "Общая поддержка";
        }
    }

    async function initializeChat() {
        try {
            const chatsRes = await fetch('/chats/my');
            const chats = await chatsRes.json();
            const activeChat = chats.find(c => c.active);

            if (activeChat) {
                currentChatId = activeChat.id;
                setupInfiniteScroll();
                await loadMessages(true);
            } else {
                chatMessages.innerHTML = `
                    <div class="message-system" id="initialPrompt">
                        Напишите сообщение, чтобы начать чат с поддержкой.
                    </div>
                `;
                currentChatId = null;
            }
            updateEndChatButtonVisibility();

        } catch (error) {
            chatMessages.innerHTML = `<div class="message-system">Ошибка: ${error.message}</div>`;
        }
    }

    async function loadMessages(reset = false) {
        if (isLoading || (!reset && !hasMore) || !currentChatId) return;

        isLoading = true;
        if (reset) {
            page = 1;
            hasMore = true;
            chatMessages.innerHTML = '<div class="message-system">Загрузка...</div>';
        }

        try {
            const url = `/messages/by_chat/${currentChatId}?page=${page}&limit=10`;
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

            const sortedData = data.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

            if (reset) {
                sortedData.forEach(msg => {
                    addMessageToChat(msg);
                });

                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                const fragment = document.createDocumentFragment();
                sortedData.reverse().forEach(msg => {
                    const messageDiv = createMessageElement(msg);
                    fragment.insertBefore(messageDiv, fragment.firstChild);
                });
                chatMessages.insertBefore(fragment, chatMessages.firstChild);
            }

            if (data.length < 10) {
                hasMore = false;
            } else {
                page++;
            }

        } catch (error) {
            if (reset) {
                chatMessages.innerHTML = `<div class="message-system">Ошибка: ${error.message}</div>`;
            }
        } finally {
            isLoading = false;
        }
    }

    function createMessageElement(msg) {
        const userId = document.querySelector('meta[name="user-id"]')?.content;
        const isUser = msg.sender_id == userId;
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

        return messageDiv;
    }

    function addMessageToChat(msg) {
        const messageDiv = createMessageElement(msg);
        chatMessages.appendChild(messageDiv);
    }

    function setupInfiniteScroll() {
        chatMessages.addEventListener('scroll', async function () {
            if (chatMessages.scrollTop === 0 && hasMore && !isLoading) {
                const currentScrollHeight = chatMessages.scrollHeight;
                await loadMessages(false);
                chatMessages.scrollTop = chatMessages.scrollHeight - currentScrollHeight;
            }
        });
    }

    function formatDateTime(isoString) {
        const date = new Date(isoString);
        return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    function updateEndChatButtonVisibility() {
    const endChatBtn = document.getElementById('endChat');
    if (endChatBtn) {
        if (currentChatId) {
            endChatBtn.style.display = 'block';
        } else {
            endChatBtn.style.display = 'none';
        }
    }
}
});
