async function updateCart(productId, isAdd, count = 1) {
    try {
        const response = await fetch('/cart/update', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: Number(productId),
                add: Boolean(isAdd),
                count: Number(count) || 1
            }),
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();

            if (result.removed) {
                const itemToRemove = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
                if (itemToRemove) {
                    itemToRemove.remove();
                }
                showToast('Товар удалён из корзины');
            } else {
                updateCartUI(productId, isAdd, count);
            }
        } else if (response.status === 401) {
            showLoginPrompt('Необходимо авторизоваться');
        } else {
            const error = await response.json();
            alert(error.detail || 'Ошибка при обновлении корзины');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при обновлении корзины');
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function updateCartUI(productId, isAdd, count) {
    console.log(productId)
    console.log(isAdd)
    console.log(count)
    const control = document.querySelector(`.quantity-control[data-product-id="${productId}"]`);
    if (!control) return;

    const quantityElement = control.querySelector('.quantity');
    if (!quantityElement) return;

    const currentCount = parseInt(quantityElement.textContent);

    if (isAdd) {
        quantityElement.textContent = currentCount + count;
    } else {
        const newCount = currentCount - count;
        if (newCount <= 0) {
            control.remove();
        } else {
            quantityElement.textContent = newCount;
        }
    }
}

function setupCartControls() {
    document.querySelectorAll('.quantity-control').forEach(control => {
        const productId = control.dataset.productId;
        const minusBtn = control.querySelector('.minus');
        const plusBtn = control.querySelector('.plus');

        const handleClick = async (e, isAdd) => {
            e.preventDefault();
            e.stopPropagation();
            await updateCart(productId, isAdd);
        };

        minusBtn.addEventListener('click', (e) => handleClick(e, false));
        plusBtn.addEventListener('click', (e) => handleClick(e, true));
    });
}

function showLoginPrompt(message) {
    if (confirm(`${message}. Перейти на страницу входа?`)) {
        window.location.href = '/auth/create';
    }
}

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
            showLoginPrompt('Необходимо авторизоваться');
        } else {
            const error = await response.json();
            alert(error.detail || 'Не удалось очистить корзину');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при очистке корзины');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setupCartControls();

    document.querySelector('.checkout-btn')?.addEventListener('click', function() {
        if (this.disabled) {
            showLoginPrompt('Для оформления заказа необходимо авторизоваться');
        } else {
            window.location.href = "{{ url_for('checkout_page') }}";
        }
    });
});