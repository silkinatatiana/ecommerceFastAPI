document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.querySelector('.messages-container');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});

async function closeChat(chatId) {
    if (!confirm('Вы уверены, что хотите завершить чат?')) {
        return;
    }

    const button = document.getElementById('closeChatBtn');
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Завершение...';

    try {
        const response = await fetch(`/chats/close?chat_id=${chatId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.status === 204) {
            button.remove();

            const statusBadge = document.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.className = 'status-badge status-closed';
                statusBadge.textContent = 'Закрыт';
            }

            alert('Чат успешно завершён.');

        } else {
            throw new Error('Ошибка при закрытии чата');
        }

    } catch (error) {
        alert('Не удалось завершить чат. Попробуйте позже.');
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-times"></i> Завершить чат';
    }
}