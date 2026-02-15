document.addEventListener('DOMContentLoaded', function() {
    initProductGrid();
    initAddButton();
    initProductCardInteractions();
});

function initProductGrid() {
    const productsGrid = document.querySelector('.products-grid');

    if (productsGrid) {
        const cards = productsGrid.querySelectorAll('.product-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(() => {
                card.style.transition = 'all 0.4s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100 * index);
        });
    }
}

function initAddButton() {
    const addButton = document.querySelector('.btn-add');

    if (addButton) {
        addButton.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
            this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
        });

        addButton.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '';
        });
    }
}

/**
 * Инициализация взаимодействий с карточками товаров
 */
function initProductCardInteractions() {
    const productCards = document.querySelectorAll('.product-card');

    productCards.forEach(card => {
        // Эффект при наведении
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.15)';
            this.style.zIndex = '10';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
            this.style.zIndex = '1';
        });

        // Клик по карточке - переход к редактированию
        card.addEventListener('click', function(e) {
            if (!e.target.closest('a, button')) {
                const productId = this.dataset.productId;
                if (productId) {
                    window.location.href = `/product/${productId}/edit`;
                }
            }
        });

        // Инициализация кнопок действий
        initCardActions(card);
    });
}

/**
 * Инициализация кнопок действий в карточке
 */
function initCardActions(card) {
    // Кнопка редактирования
    const editBtn = card.querySelector('.btn-edit');
    if (editBtn) {
        editBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const productId = card.dataset.productId;
            window.location.href = `/product/${productId}/edit`;
        });
    }

    // Кнопка удаления
    const deleteBtn = card.querySelector('.btn-delete');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            handleDeleteProduct(card);
        });
    }

    // Кнопка избранного
    const favoriteBtn = card.querySelector('.btn-favorite');
    if (favoriteBtn) {
        favoriteBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleFavorite(card, favoriteBtn);
        });
    }
}

/**
 * Обработка удаления товара
 */
function handleDeleteProduct(card) {
    const productId = card.dataset.productId;

    if (!confirm('Вы уверены, что хотите удалить этот товар?')) {
        return;
    }

    // Показываем индикатор загрузки
    showLoadingIndicator(card);

    fetch(`/api/products/${productId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при удалении товара');
        }
        return response.json();
    })
    .then(data => {
        // Удаляем карточку с анимацией
        removeProductCard(card);
    })
    .catch(error => {
        hideLoadingIndicator(card);
        showError('Не удалось удалить товар: ' + error.message);
    });
}

/**
 * Переключение избранного статуса
 */
function toggleFavorite(card, button) {
    const productId = card.dataset.productId;
    const isFavorite = button.classList.contains('active');

    // Показываем индикатор загрузки
    button.disabled = true;
    button.innerHTML = isFavorite ? '💔' : '❤️';

    fetch(`/api/products/${productId}/favorite`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify({ favorite: !isFavorite })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при обновлении избранного');
        }
        return response.json();
    })
    .then(data => {
        // Обновляем состояние кнопки
        if (data.favorite) {
            button.classList.add('active');
            button.innerHTML = '❤️';
        } else {
            button.classList.remove('active');
            button.innerHTML = '🤍';
        }
    })
    .catch(error => {
        showError('Не удалось обновить избранное: ' + error.message);
    })
    .finally(() => {
        button.disabled = false;
    });
}

/**
 * Удаление карточки товара с анимацией
 */
function removeProductCard(card) {
    card.style.transition = 'all 0.3s ease';
    card.style.opacity = '0';
    card.style.transform = 'scale(0.9)';

    setTimeout(() => {
        card.remove();

        // Проверяем, остались ли товары
        const productsGrid = document.querySelector('.products-grid');
        if (productsGrid && productsGrid.children.length === 0) {
            showEmptyState();
        }
    }, 300);
}

/**
 * Показ пустого состояния
 */
function showEmptyState() {
    const container = document.querySelector('.container');
    if (!container) return;

    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">У вас пока нет товаров</div>
            <a href="/create" class="btn btn-primary">Добавить товар</a>
        </div>
    `;
}

/**
 * Показ индикатора загрузки
 */
function showLoadingIndicator(element) {
    const loader = document.createElement('div');
    loader.className = 'loading-indicator';
    loader.innerHTML = '<div class="spinner"></div>';
    element.appendChild(loader);
}

/**
 * Скрытие индикатора загрузки
 */
function hideLoadingIndicator(element) {
    const loader = element.querySelector('.loading-indicator');
    if (loader) {
        loader.remove();
    }
}

/**
 * Показ ошибки
 */
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-error';
    errorDiv.textContent = message;
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '20px';
    errorDiv.style.right = '20px';
    errorDiv.style.zIndex = '1000';
    errorDiv.style.padding = '12px 20px';
    errorDiv.style.backgroundColor = '#ff4444';
    errorDiv.style.color = 'white';
    errorDiv.style.borderRadius = '4px';
    errorDiv.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)';

    document.body.appendChild(errorDiv);

    setTimeout(() => {
        errorDiv.style.opacity = '0';
        errorDiv.style.transition = 'opacity 0.3s ease';
        setTimeout(() => errorDiv.remove(), 300);
    }, 3000);
}

/**
 * Получение CSRF токена
 */
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

/**
 * Фильтрация товаров (если понадобится)
 */
function filterProducts(category) {
    const cards = document.querySelectorAll('.product-card');

    cards.forEach(card => {
        const productCategory = card.querySelector('.product-category')?.textContent;

        if (category === 'all' || !category) {
            card.style.display = 'block';
        } else {
            card.style.display = productCategory === category ? 'block' : 'none';
        }
    });
}

/**
 * Сортировка товаров (если понадобится)
 */
function sortProducts(criteria) {
    const productsGrid = document.querySelector('.products-grid');
    if (!productsGrid) return;

    const cards = Array.from(productsGrid.children);

    cards.sort((a, b) => {
        switch(criteria) {
            case 'price-asc':
                return parseFloat(a.querySelector('.product-price').textContent) -
                       parseFloat(b.querySelector('.product-price').textContent);
            case 'price-desc':
                return parseFloat(b.querySelector('.product-price').textContent) -
                       parseFloat(a.querySelector('.product-price').textContent);
            case 'name':
                return a.querySelector('.product-name').textContent.localeCompare(
                    b.querySelector('.product-name').textContent
                );
            case 'stock':
                const aStock = parseInt(a.querySelector('.product-stock')?.textContent || '0');
                const bStock = parseInt(b.querySelector('.product-stock')?.textContent || '0');
                return bStock - aStock;
            default:
                return 0;
        }
    });

    // Очищаем и добавляем отсортированные карточки
    productsGrid.innerHTML = '';
    cards.forEach(card => productsGrid.appendChild(card));
}