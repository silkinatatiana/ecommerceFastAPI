document.addEventListener('DOMContentLoaded', function() {
    initializeOrderPage();
    setupEventListeners();
});

function initializeOrderPage() {
    console.log('Initializing order page...');

    autoExpandProducts();

    setupImageErrorHandling();

    setupAccessibility();

    restoreSavedState();

    if (isDevelopmentMode()) {
        enableDeveloperTools();
    }

    console.log('Order page initialized successfully');
}

function setupEventListeners() {
    const expandButton = document.querySelector('.expand-toggle');
    if (expandButton) {
        expandButton.addEventListener('click', handleExpandToggle);
        expandButton.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleExpandToggle();
            }
        });
    }

    setupProductItemsInteractions();

    const backButton = document.querySelector('.btn-primary');
    if (backButton) {
        backButton.addEventListener('click', handleBackButtonClick);
    }

    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handlePromiseRejection);
}

//function handleExpandToggle(event) {
//    if (event) {
//        event.stopPropagation();
//        event.preventDefault();
//    }
//
//    const content = document.getElementById('productsContent');
//    const icon = document.querySelector('.toggle-icon');
//
//    console.log('Toggle elements:', {content, icon}); // Для отладки
//
//    if (!content || !icon) {
//        console.error('Required elements not found');
//        return;
//    }
//
//    const isExpanding = !content.classList.contains('expanded');
//
//    if (isExpanding) {
//        content.style.display = 'block';
//        requestAnimationFrame(() => {
//            content.style.height = content.scrollHeight + 'px';
//            content.classList.add('expanded');
//            icon.classList.add('expanded');
//        });
//    } else {
//        content.style.height = '0';
//        content.classList.remove('expanded');
//        icon.classList.remove('expanded');
//
//        setTimeout(() => {
//            content.style.display = 'none';
//            content.style.height = 'auto';
//        }, 300);
//    }
//
//    localStorage.setItem('orderProductsExpanded', isExpanding.toString());
//}

function expandProducts(content, icon) {
    content.style.display = 'block';
    content.style.height = '0';
    content.classList.add('expanded');
    icon.classList.add('expanded');

    const contentHeight = content.scrollHeight;
    content.style.height = contentHeight + 'px';

    setTimeout(() => {
        content.style.height = 'auto';
    }, 300);
}

function collapseProducts(content, icon) {
    const contentHeight = content.scrollHeight;
    content.style.height = contentHeight + 'px';

    requestAnimationFrame(() => {
        content.style.height = '0';
        content.classList.remove('expanded');
        icon.classList.remove('expanded');
    });

    setTimeout(() => {
        content.style.display = 'none';
        content.style.height = 'auto';
    }, 300);
}

function autoExpandProducts() {
    const productCount = document.querySelectorAll('.product-item').length;
    const shouldAutoExpand = productCount > 0 && productCount <= 3;

    if (shouldAutoExpand) {
        setTimeout(() => {
            handleExpandToggle();
        }, 500);
    }
}

function setupProductItemsInteractions() {
    const productItems = document.querySelectorAll('.product-item');

    productItems.forEach((item, index) => {
        item.setAttribute('tabindex', '0');
        item.setAttribute('role', 'link');
        item.setAttribute('aria-label', `Товар ${index + 1}`);

        item.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });

        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
            this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        });

        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
            this.style.boxShadow = 'none';
        });

        item.addEventListener('click', function() {
            trackProductClick(this.href, index + 1);
        });
    });
}

function handleBackButtonClick(e) {
    e.preventDefault();
    const button = e.currentTarget;

    // Показываем индикатор загрузки
    setLoadingState(button, true);

    // Аналитика
    trackUserAction('back_to_orders');

    // Переход с задержкой для плавности
    setTimeout(() => {
        window.location.href = button.onclick.toString().match(/\/orders\/user\d+/)[0];
    }, 200);
}

function formatPrice(price, currency = 'RUB') {
    if (typeof price !== 'number') {
        price = parseFloat(price) || 0;
    }

    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(price);
}

function formatDate(dateString, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Date(dateString).toLocaleDateString('ru-RU', mergedOptions);
}

function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.setAttribute('disabled', 'true');
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
        element.style.opacity = '0.7';
    } else {
        element.removeAttribute('disabled');
        element.innerHTML = element.getAttribute('data-original-text') || 'Вернуться к списку заказов';
        element.style.opacity = '1';
    }
}

function handlePromiseRejection(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--error-color);
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        z-index: 1000;
        max-width: 300px;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function setupImageErrorHandling() {
    const images = document.querySelectorAll('img');

    images.forEach(img => {
        // Сохраняем оригинальный src
        if (!img.hasAttribute('data-original-src')) {
            img.setAttribute('data-original-src', img.src);
        }

        img.addEventListener('error', handleImageError);
        img.addEventListener('load', handleImageLoad);
    });
}

function handleImageError(event) {
    const img = event.target;
    console.warn('Image failed to load:', img.src);

    // Пытаемся загрузить placeholder
    img.src = '/static/images/placeholder-product.jpg';
    img.alt = 'Изображение не найдено';
    img.style.opacity = '0.7';
}

function handleImageLoad(event) {
    const img = event.target;
    img.style.opacity = '1';
}

function setupAccessibility() {
    // Добавляем aria-атрибуты
    const expandButton = document.querySelector('.expand-toggle');
    if (expandButton) {
        expandButton.setAttribute('aria-expanded', 'false');
        expandButton.setAttribute('role', 'button');
    }

    // Настройка focus management
    setupFocusManagement();

    // Keyboard shortcuts
    setupKeyboardShortcuts();
}

function setupFocusManagement() {
    // Сохраняем последний активный элемент
    let lastFocusedElement;

    document.addEventListener('focusin', function(e) {
        lastFocusedElement = e.target;
    });

    // Восстановление фокуса после взаимодействия с модальными окнами
    window.restoreFocus = function() {
        if (lastFocusedElement) {
            lastFocusedElement.focus();
        }
    };
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === '1') {
            e.preventDefault();
            document.querySelector('main')?.focus();
        }

        if (e.altKey && e.key === '2') {
            e.preventDefault();
            document.querySelector('.nav')?.focus();
        }
    });
}

function saveExpandState(isExpanded) {
    try {
        localStorage.setItem('orderProductsExpanded', isExpanded.toString());
    } catch (error) {
        console.warn('Failed to save state to localStorage:', error);
    }
}

function restoreSavedState() {
    try {
        const savedState = localStorage.getItem('orderProductsExpanded');
        if (savedState === 'true') {
            const content = document.getElementById('productsContent');
            const icon = document.querySelector('.toggle-icon');
            if (content && icon) {
                content.classList.add('expanded');
                icon.classList.add('expanded');
            }
        }
    } catch (error) {
        console.warn('Failed to restore state from localStorage:', error);
    }
}

function trackUserAction(action, data = {}) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            ...data,
            page_title: document.title,
            page_location: window.location.href
        });
    }

    console.log('User action:', action, data);
}

function trackProductClick(url, position) {
    trackUserAction('product_click', {
        product_url: url,
        product_position: position,
        order_id: getOrderIdFromUrl()
    });
}

function getOrderIdFromUrl() {
    const match = window.location.pathname.match(/\/orders\/(\d+)/);
    return match ? match[1] : null;
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
            const result = await response.json();
            alert(result.message || 'Заказ успешно отменен');

            const orderCard = document.querySelector(`[data-order-id="${orderId}"]`);
            if (orderCard) {
                const statusElement = orderCard.querySelector('.order-status');
                statusElement.textContent = 'Отменен';
                statusElement.className = 'order-status';
                statusElement.style.backgroundColor = '#ffebee';
                statusElement.style.color = '#d32f2f';

                const cancelButton = orderCard.querySelector('.btn-cancel');
                cancelButton.disabled = true;
                cancelButton.textContent = 'Заказ отменен';
            }
        } else {
            const errorData = await response.json();
            alert(`Ошибка: ${errorData.detail || 'Не удалось отменить заказ'}`);
        }
    } catch (error) {
        console.error('Ошибка при отмене заказа:', error);
        alert('Произошла ошибка при отмене заказа');
    }
}
