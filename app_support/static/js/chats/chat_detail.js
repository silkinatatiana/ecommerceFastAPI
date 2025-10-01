function toggleClientInfo(event) {
    event.preventDefault();
    const popup = document.getElementById('client-info-popup');
    popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
}

function closeClientInfo() {
    document.getElementById('client-info-popup').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.messages-area');
    container.scrollTop = container.scrollHeight;
});

async function completeChat(chatId) {
    if (!confirm('Вы уверены, что хотите завершить чат?')) {
        return;
    }

    try {
        const response = await fetch(`/support/chats/${chatId}/complete`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            alert('Чат успешно завершён');
            window.location.reload();
        } else {
            const errorText = await response.text();
            alert('Ошибка: ' + (errorText || 'Не удалось завершить чат'));
        }
    } catch (error) {
        console.error('Ошибка при завершении чата:', error);
        alert('Произошла ошибка при подключении к серверу');
    }
}