document.addEventListener('DOMContentLoaded', function () {
    initializeOrderPage();
    setupEventListeners();
});

function initializeOrderPage() {
    console.log('Initializing order page...');

    setupImageErrorHandling();

    console.log('Order page initialized successfully');
}

function setupEventListeners() {
    setupProductItemsInteractions();
}

async function cancelOrder(orderId) {
    if (!confirm('Вы уверены, что хотите отменить заказ?')) {
        return;
    }

    try {
        const response = await fetch(`/orders/cancel_order/${orderId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });

        if (response.ok) {
            alert('Заказ успешно отменён.');
            window.location.reload();
        } else {
            const errorData = await response.json().catch(() => ({}));
            alert(`Ошибка: ${errorData.detail || 'Не удалось отменить заказ'}`);
        }
    } catch (error) {
        console.error('Ошибка при отмене заказа:', error);
        alert('Произошла ошибка при отмене заказа. Попробуйте позже.');
    }
}

function setupImageErrorHandling() {
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function () {
            this.src = '/static/images/placeholder-product.jpg';
            this.alt = 'Изображение недоступно';
        });
    });
}

function setupProductItemsInteractions() {
    document.querySelectorAll('.product-item').forEach((item, index) => {
        item.setAttribute('tabindex', '0');
        item.setAttribute('role', 'link');
        item.setAttribute('aria-label', `Товар ${index + 1}`);

        item.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });

        item.addEventListener('mouseenter', () => {
            item.style.transform = 'translateX(5px)';
            item.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        });
        item.addEventListener('mouseleave', () => {
            item.style.transform = 'translateX(0)';
            item.style.boxShadow = 'none';
        });
    });
}

function handleExpandToggle() {
    const content = document.querySelector('.expandable-section');
    if (!content) return;

    const isExpanded = content.style.display !== 'none' && content.style.display !== '';

    if (isExpanded) {
        content.style.display = 'none';
    } else {
        content.style.display = 'block';
    }
}