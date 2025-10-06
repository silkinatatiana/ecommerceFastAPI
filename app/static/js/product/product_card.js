async function removeFromCart(productId) {
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

async function addProduct(productId, count = 1) {
    try {
        const response = await fetch('/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'include',
            body: JSON.stringify({
                product_id: parseInt(productId),
                count: parseInt(count)
            })
        });

        if (response.status === 401) {
            const loginConfirmed = confirm('Сессия истекла. Войдите снова.');
            if (loginConfirmed) {
                window.location.href = '/login';
            }
            return;
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при добавлении в корзину');
        }

        const result = await response.json();
        location.reload();

    } catch (error) {
        console.error('Ошибка:', error);
        alert(error.message || 'Произошла ошибка при добавлении в корзину');
    }
}
