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
                    updateTotalPrice();
                }
                showToast('Товар удалён из корзины');
                setTimeout(() => {
                    window.location.reload();
                }, 800);
            } else {
                updateCartUI(productId, isAdd, count);
                updateTotalPrice();
                setTimeout(() => {
                    window.location.reload();
                }, 300);
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

function updateTotalPrice() {
    const priceElements = document.querySelectorAll('.cart-item-price');
    let total = 0;

    priceElements.forEach(el => {
        const price = parseFloat(el.textContent.replace(/[^\d.,]/g, '').replace(',', '.'));
        const quantity = parseInt(el.closest('.cart-item').querySelector('.quantity').textContent);
        total += price * quantity;
    });

    const totalElement = document.querySelector('.cart-total-price');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2) + ' ₽';
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
            localStorage.removeItem('token');
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

function showLoginPrompt(message) {
    const loginConfirmed = confirm(`${message}. Перейти на страницу входа?`);
    if (loginConfirmed) {
        window.location.href = '/auth/create';
    }
}

async function proceedToCheckout() {
    try {
        // Проверяем, что корзина не пуста
        const response = await fetch('/cart', {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Не удалось проверить корзину');
        }

        const cartData = await response.json();

        if (!cartData.products || cartData.products.length === 0) {
            alert('Корзина пуста');
            return;
        }

        window.location.href = '/orders';

    } catch (error) {
        console.error('Error proceeding to checkout:', error);
        alert('Ошибка при переходе к оформлению заказа');
    }
}