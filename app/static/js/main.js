async function loadMoreProducts(categoryId, button) {
    const currentSkip = parseInt(button.dataset.skip); // Уже загруженное количество
    const categoryElement = button.closest('.category');
    const productsGrid = categoryElement.querySelector('.products-grid');

    button.disabled = true;
    button.textContent = 'Загрузка...';

    try {
        const params = new URLSearchParams({
            category_id: categoryId,
            skip: currentSkip, // Передаем уже загруженное количество
            limit: 10
        });

        // Добавляем активные фильтры
        const activeFilters = getActiveFilters();
        Object.entries(activeFilters).forEach(([key, value]) => {
            if (value) params.append(key, value);
        });

        const response = await fetch(`/products/load-more/?${params.toString()}`, {
            headers: {
                'Accept': 'text/html',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) throw new Error('Ошибка загрузки');

        const html = await response.text();
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;

        // Добавляем только новые товары
        const productCards = tempDiv.querySelectorAll('.product-card');
        if (productCards.length === 0) {
            button.style.display = 'none'; // Нет больше товаров
        } else {
            productCards.forEach(card => {
                productsGrid.appendChild(card);
            });

            // Обновляем счетчик загруженных товаров
            button.dataset.skip = currentSkip + productCards.length;
        }

        // Проверяем, есть ли еще товары
        const hasMorePlaceholder = tempDiv.querySelector('.load-more-placeholder');
        if (!hasMorePlaceholder) {
            button.style.display = 'none'; // Скрываем кнопку если больше нет товаров
        }

    } catch (error) {
        console.error('Ошибка загрузки:', error);
        button.textContent = 'Ошибка, попробовать снова';
        setTimeout(() => {
            button.textContent = 'Показать еще товары';
        }, 2000);
    } finally {
        button.disabled = false;
        button.textContent = 'Показать еще товары';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.view-all-btn').forEach(button => {
        const categoryId = button.dataset.categoryId;
        const skip = parseInt(button.dataset.skip);

        const loadMoreContainer = document.createElement('div');
        loadMoreContainer.className = 'load-more-container';
        loadMoreContainer.dataset.categoryId = categoryId;
        loadMoreContainer.dataset.skip = skip;

        button.parentElement.appendChild(loadMoreContainer);
    });
});

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