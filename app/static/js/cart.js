async function removeFromCart(productId) {
        if (!confirm('Вы уверены, что хотите удалить товар из корзины?')) return;
        console.log(productId)
        try {
            const response = await fetch(`/cart/${productId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (response.ok) {
                location.reload();
            } else {
                const error = await response.json();
                alert(error.detail || 'Не удалось удалить товар из корзины');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при удалении товара');
        }
    }

async function updateQuantity(productId, change) {
    try {
        const response = await fetch(`/cart/${productId}/quantity`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ change }),
            credentials: 'include'
        });

        if (response.ok) {
            location.reload();
        } else {
            const error = await response.json();
            alert(error.detail || 'Не удалось изменить количество');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при изменении количества');
    }
}

document.querySelector('.checkout-btn')?.addEventListener('click', function() {
    if (this.disabled) {
        alert('Для оформления заказа необходимо авторизоваться');
        window.location.href = "{{ url_for('create_auth_form') }}";
    } else {
        window.location.href = "{{ url_for('checkout_page') }}";
    }
});

async function clearCart() {
    if (!confirm('Вы уверены, что хотите очистить всю корзину?')) return;

    try {
        const response = await fetch('/cart/clear', {
            method: 'POST',
            credentials: 'include'
        });

        if (response.status === 204) {
            location.reload();
        } else if (response.status === 401) {
            alert('Необходимо авторизоваться');
            window.location.href = '/login';
        } else {
            const error = await response.json();
            alert(error.detail || 'Не удалось очистить корзину');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при очистке корзины');
    }
}

