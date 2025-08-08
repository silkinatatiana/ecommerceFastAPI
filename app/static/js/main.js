async function loadAllProducts(categoryId, button) {
    const skip = parseInt(button.dataset.skip);
    const container = document.getElementById(`products-${Array.isArray(categoryId) ? categoryId[0] : categoryId}`);
    const mainGrid = button.closest('.category').querySelector('.products-grid');
    const hideBtn = button.parentElement.querySelector('.hide-btn');

    container.innerHTML = '<p>Загрузка...</p>';
    button.disabled = true;

    try {
        const params = new URLSearchParams();

        // Базовые параметры
        if (Array.isArray(categoryId)) {
            categoryId.forEach(id => params.append('categoryId', id));
        } else {
            params.append('categoryId', categoryId);
        }
        params.append('skip', skip);

        // Параметры избранного
        const favoritesOnly = document.getElementById('favoritesOnlyCheckbox');
        if (favoritesOnly && favoritesOnly.checked) {
            params.append('is_favorite', 'true');

            // Получаем user_id из мета-тега или куки
            const userMeta = document.querySelector('meta[name="user-id"]');
            const user_id = userMeta ? userMeta.content : getCookie('user_id');

            if (user_id) {
                params.append('user_id', user_id);
            } else {
                console.warn('User ID not found for favorites filter');
                throw new Error('Требуется авторизация для просмотра избранного');
            }
        }

        // Добавляем другие активные фильтры
        const activeFilters = getActiveFilters(); // Функция собирает все активные фильтры
        Object.entries(activeFilters).forEach(([key, value]) => {
            params.append(key, value);
        });

        const response = await fetch(`/products/by_category/?${params.toString()}`, {
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'include' // Для передачи кук
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка загрузки');
        }

        const additionalProducts = await response.json();

        // Обработка пустого результата
        if (additionalProducts.length === 0) {
            container.innerHTML = '<p class="no-products">Нет дополнительных товаров</p>';
            button.style.display = 'none';
            return;
        }

        // Отрисовка товаров
        additionalProducts.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card additional-product';
            productCard.dataset.category = product.category_id;
            productCard.dataset.id = product.id;

            productCard.innerHTML = `
                <img src="${product.image_urls?.[0] || '/static/images/default_image.png'}"
                    alt="${product.name}"
                    loading="lazy"
                    onerror="this.onerror=null;this.src='/static/images/default_image.png'">
                <div class="product-info">
                    <h3>${product.name}</h3>
                    <p class="product-price">${product.price ? `${product.price} ₽` : 'Цена не указана'}</p>
                    <p class="product-stock ${product.stock <= 0 ? 'out-of-stock' : ''}">
                        ${product.stock} шт. в наличии
                    </p>
                    ${product.is_favorite ? '<div class="favorite-badge">★</div>' : ''}
                </div>
            `;

            productCard.addEventListener('click', (e) => {
                if (!e.target.closest('.favorite-toggle')) {
                    window.location.href = `/products/${product.id}`;
                }
            });

            mainGrid.appendChild(productCard);
        });

        // Обновляем состояние кнопок
        button.dataset.skip = skip + additionalProducts.length;
        hideBtn.style.display = 'inline-block';

        if (additionalProducts.length < 6) {
            button.style.display = 'none';
        }

    } catch (error) {
        console.error('Ошибка:', error);
        container.innerHTML = `
            <div class="load-error">
                <p>${error.message}</p>
                <button onclick="window.location.reload()">Попробовать снова</button>
            </div>
        `;

        if (error.message.includes('авторизация')) {
            // Перенаправляем на страницу входа, если требуется авторизация
            setTimeout(() => window.location.href = '/login', 2000);
        }
    } finally {
        button.disabled = false;
        container.innerHTML = '';
    }
}

function getActiveFilters() {
    const filters = {};

    document.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
        if (checkbox.name && checkbox.value) {
            if (filters[checkbox.name]) {
                filters[checkbox.name] += `,${checkbox.value}`;
            } else {
                filters[checkbox.name] = checkbox.value;
            }
        }
    });

    return filters;
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function hideProducts(categoryId, button) {
    const viewAllBtn = button.parentElement.querySelector('.view-all-btn');
    const mainGrid = button.closest('.category').querySelector('.products-grid');

    const additionalProducts = mainGrid.querySelectorAll(`.additional-product[data-category="${categoryId}"]`);
    additionalProducts.forEach(product => product.remove());

    viewAllBtn.style.display = 'inline-block';
    viewAllBtn.dataset.skip = 6;
    button.style.display = 'none';
}

function toggleFilter() {
    const dropdown = document.getElementById('categoryDropdown');
    dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

function updateFilterButton(categoryName) {
    const button = document.getElementById('categoryFilterButton');
    button.textContent = categoryName;
}

function applyFilters() {
    const params = new URLSearchParams();

    // Категории
    const categoryCheckboxes = document.querySelectorAll('input[name="category"]:checked');
    if (categoryCheckboxes.length > 0) {
        params.append('category_id', Array.from(categoryCheckboxes).map(cb => cb.value).join(','));
    }

    // Цвета
    const colorCheckboxes = document.querySelectorAll('input[name="color"]:checked');
    if (colorCheckboxes.length > 0) {
        params.append('colors', Array.from(colorCheckboxes).map(cb => cb.value).join(','));
    }

    // Память
    const memoryCheckboxes = document.querySelectorAll('input[name="built_in_memory"]:checked');
    if (memoryCheckboxes.length > 0) {
        params.append('built_in_memory', Array.from(memoryCheckboxes).map(cb => cb.value).join(','));
    }

    // Избранное
    const favoritesCheckbox = document.getElementById('favoritesOnlyCheckbox');
     if (favoritesCheckbox) {
        if (favoritesCheckbox.checked) {
            params.set('is_favorite', 'true');
        } else {
            params.delete('is_favorite');
        }
    }

    // Обновляем URL без перезагрузки страницы
    window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);

    // Принудительная перезагрузка для применения фильтров
    window.location.search = params.toString();
}

function resetFilters() {
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });

    window.history.pushState({}, '', window.location.pathname);

    window.location.href = window.location.pathname;
}

async function loadFilteredProducts() {
    const productsContainer = document.getElementById('products-container');
    productsContainer.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const params = new URLSearchParams(window.location.search);

        // Добавляем user_id если есть
        const userMeta = document.querySelector('meta[name="user-id"]');
        if (userMeta && params.get('is_favorite') === 'true') {
            params.append('user_id', userMeta.content);
        }

        const response = await fetch(`/products/filtered?${params.toString()}`);

        if (!response.ok) throw new Error(await response.text());

        const products = await response.json();
        renderProducts(products);

    } catch (error) {
        console.error('Ошибка загрузки:', error);
        productsContainer.innerHTML = `
            <div class="error-message">
                ${error.message}
                <button onclick="loadFilteredProducts()">Повторить</button>
            </div>
        `;
    }
}

function initFiltersFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);

    // Категории
    const categoryParam = urlParams.get('category_id');
    if (categoryParam) {
        const categories = categoryParam.split(',');
        categories.forEach(cat => {
            const checkbox = document.querySelector(`input[name="category"][value="${cat}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    // Избранное
    const favoritesOnly = urlParams.get('is_favorite');
    if (favoritesOnly === 'true') {
        const checkbox = document.getElementById('favoritesOnlyCheckbox');
        if (checkbox) checkbox.checked = true;
    }

    // Цвета
    const colorParam = urlParams.get('colors');
    if (colorParam) {
        const colors = colorParam.split(',');
        colors.forEach(color => {
            const checkbox = document.querySelector(`input[name="color"][value="${color}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    // Память
    const memoryParam = urlParams.get('built_in_memory');
    if (memoryParam) {
        const memories = memoryParam.split(',');
        memories.forEach(mem => {
            const checkbox = document.querySelector(`input[name="built_in_memory"][value="${mem}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initFiltersFromUrl();

    const userIcon = document.getElementById('userIcon');
    const dropdown = document.getElementById('userDropdown');

    if (userIcon && dropdown) {
        userIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdown.classList.toggle('show-dropdown');
        });

        document.addEventListener('click', function() {
            dropdown.classList.remove('show-dropdown');
        });
    }
});

async function toggleFavorite(element, productId) {

    try {
        const response = await fetch(`/favorites/toggle/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'  // Важно для отправки кук
        });

        if (response.ok) {
            const data = await response.json();
            element.querySelector('.heart-icon').classList.toggle('active');
        } else {
            console.error('Ошибка при обновлении избранного:', response.status);
            if (response.status === 401) {
                showAuthModal();
            }
        }
    } catch (error) {
        console.error('Ошибка сети:', error);
    }
}