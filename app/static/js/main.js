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
    if (favoritesCheckbox && favoritesCheckbox.checked) {
        params.append('is_favorite', 'true');
    }

    // Обновляем URL и перезагружаем страницу
    window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
    window.location.search = params.toString();
}

function resetFilters() {
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });

    window.history.pushState({}, '', window.location.pathname);
    window.location.href = window.location.pathname;
}

async function loadMoreProducts(categoryId, buttonElement) {
    const currentSkip = parseInt(buttonElement.getAttribute('data-skip')) || 0;
    const limit = parseInt(buttonElement.getAttribute('data-limit')) || 12;

    try {
        const params = new URLSearchParams();
        params.append('category_id', categoryId);
        params.append('skip', currentSkip.toString());
        params.append('limit', limit.toString());

        document.querySelectorAll('input[name="category"]:checked').forEach(input => {
            params.append('categories', input.value);
        });

        document.querySelectorAll('input[name="built_in_memory"]:checked').forEach(input => {
            params.append('built_in_memory', input.value);
        });

        document.querySelectorAll('input[name="color"]:checked').forEach(input => {
            params.append('colors', input.value);
        });

        if (document.getElementById('favoritesOnlyCheckbox')?.checked) {
            params.append('is_favorite', 'true');
        }

        const response = await fetch(`/products/load-more/?${params.toString()}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const html = await response.text();

        if (html.trim()) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;

            const productsGrid = buttonElement.closest('.category').querySelector('.products-grid');
            const newProducts = tempDiv.querySelectorAll('.product-card');

            newProducts.forEach(product => {
                productsGrid.appendChild(product.cloneNode(true));
            });

            const placeholder = tempDiv.querySelector('.load-more-placeholder');
            if (placeholder) {
                const nextSkip = parseInt(placeholder.getAttribute('data-skip')) || currentSkip;
                buttonElement.setAttribute('data-skip', nextSkip.toString());

                const initialSkip = parseInt(buttonElement.getAttribute('data-initial-skip')) || 0;
                if (nextSkip > initialSkip) {
                    const collapseBtn = buttonElement.closest('.category-actions').querySelector('.collapse-btn');
                    if (collapseBtn) {
                        collapseBtn.style.display = 'inline-block';
                    }
                }
            } else {
                buttonElement.style.display = 'none';

                const collapseBtn = buttonElement.closest('.category-actions').querySelector('.collapse-btn');
                if (collapseBtn) {
                    collapseBtn.style.display = 'inline-block';
                }
            }
        }

    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
        alert('Произошла ошибка при загрузке товаров');
    }
}

function collapseProducts(categoryId, buttonElement) {
    const categoryElement = buttonElement.closest('.category');
    const productsGrid = categoryElement.querySelector('.products-grid');
    const loadMoreBtn = categoryElement.querySelector('.load-more-btn');
    const initialSkip = parseInt(loadMoreBtn.getAttribute('data-initial-skip')) || 3;

    const allProducts = Array.from(productsGrid.querySelectorAll('.product-card'));
    allProducts.forEach((product, index) => {
        if (index >= initialSkip) {
            product.remove();
        }
    });

    if (loadMoreBtn) {
        loadMoreBtn.setAttribute('data-skip', initialSkip.toString());
        loadMoreBtn.style.display = 'inline-block';
    }

    buttonElement.style.display = 'none';
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

    // Проверяем, есть ли активные фильтры (кроме category_id)
    const hasActiveFilters = favoritesOnly === 'true' || colorParam || memoryParam;
    if (hasActiveFilters) {
        hideCategoryTitles();
    }
}

function hideCategoryTitles() {
    const categoryTitles = document.querySelectorAll('.category h3');
    categoryTitles.forEach(title => {
        title.style.display = 'none';
    });
}

function showCategoryTitles() {
    const categoryTitles = document.querySelectorAll('.category h3');
    categoryTitles.forEach(title => {
        title.style.display = 'block';
    });
}

function processFavoritesFilter() {
    const favoritesCheckbox = document.getElementById('favoritesOnlyCheckbox');
    const isFavoriteFilterActive = favoritesCheckbox && favoritesCheckbox.checked;

    if (!isFavoriteFilterActive) {
        // Если фильтр избранного не активен - показываем все как есть
        showAllContent();
        return;
    }

    // Если фильтр избранного активен
    const favoriteProducts = document.querySelectorAll('.product-card .heart-icon.active');
    const hasFavorites = favoriteProducts.length > 0;

    if (hasFavorites) {
        // Есть избранные товары - показываем только их
        showOnlyFavorites();
    } else {
        // Нет избранных товаров - показываем сообщение
        showNoFavoritesMessage();
    }
}

function showAllContent() {
    // Показываем все категории и товары
    const categories = document.querySelectorAll('.category');
    categories.forEach(category => {
        category.style.display = 'block';
    });

    const products = document.querySelectorAll('.product-card');
    products.forEach(product => {
        product.style.display = 'block';
    });

    // Показываем заголовки категорий только если нет активных фильтров
    const urlParams = new URLSearchParams(window.location.search);
    const hasActiveFilters = urlParams.get('is_favorite') === 'true' ||
                           urlParams.get('colors') ||
                           urlParams.get('built_in_memory');

    if (hasActiveFilters) {
        hideCategoryTitles();
    } else {
        showCategoryTitles();
    }

    // Убираем сообщение об отсутствии избранного
    const noFavoritesMessage = document.querySelector('.no-favorites-message');
    if (noFavoritesMessage) {
        noFavoritesMessage.remove();
    }
}

function showOnlyFavorites() {
    const categories = document.querySelectorAll('.category');
    let hasVisibleCategories = false;

    // Скрываем все заголовки категорий
    hideCategoryTitles();

    categories.forEach(category => {
        const products = category.querySelectorAll('.product-card');
        let hasFavoriteInCategory = false;

        products.forEach(product => {
            const heartIcon = product.querySelector('.heart-icon.active');
            if (heartIcon) {
                product.style.display = 'block';
                hasFavoriteInCategory = true;
            } else {
                product.style.display = 'none';
            }
        });

        if (hasFavoriteInCategory) {
            category.style.display = 'block';
            hasVisibleCategories = true;
        } else {
            category.style.display = 'none';
        }
    });

    // Убираем сообщение об отсутствии избранного
    const noFavoritesMessage = document.querySelector('.no-favorites-message');
    if (noFavoritesMessage) {
        noFavoritesMessage.remove();
    }

    // Если нет видимых категорий (все избранные товары скрыты)
    if (!hasVisibleCategories) {
        showNoFavoritesMessage();
    }
}

function showNoFavoritesMessage() {
    // Скрываем все категории
    const categories = document.querySelectorAll('.category');
    categories.forEach(category => {
        category.style.display = 'none';
    });

    // Проверяем, нет ли уже сообщения
    const existingMessage = document.querySelector('.no-favorites-message');
    if (existingMessage) {
        return;
    }

    // Создаем сообщение
    const contentArea = document.querySelector('.content-area');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'no-favorites-message no-products-found';
    messageDiv.innerHTML = `
        <p>В избранном пока нет товаров</p>
        <p>Добавьте товары в избранное, чтобы они отображались здесь</p>
        <button class="reset-filters" onclick="resetFilters()">Сбросить фильтры</button>
    `;

    contentArea.appendChild(messageDiv);
}

// Функция для проверки состояния избранного при загрузке
function checkFavoritesOnLoad() {
    const urlParams = new URLSearchParams(window.location.search);
    const isFavoriteFilterActive = urlParams.get('is_favorite') === 'true';

    // Проверяем все фильтры
    const hasActiveFilters = isFavoriteFilterActive ||
                           urlParams.get('colors') ||
                           urlParams.get('built_in_memory');

    if (hasActiveFilters) {
        hideCategoryTitles();
    }

    if (isFavoriteFilterActive) {
        // Даем время на загрузку всех товаров
        setTimeout(() => {
            processFavoritesFilter();
        }, 1000);
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

    // Обработчик для checkbox избранного - с перезагрузкой
    const favoritesCheckbox = document.getElementById('favoritesOnlyCheckbox');
    if (favoritesCheckbox) {
        favoritesCheckbox.addEventListener('change', function() {
            const params = new URLSearchParams(window.location.search);

            if (this.checked) {
                params.set('is_favorite', 'true');
            } else {
                params.delete('is_favorite');
            }

            // Обновляем URL и перезагружаем страницу
            window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            window.location.search = params.toString();
        });
    }

    // Проверяем избранное при загрузке
    checkFavoritesOnLoad();

    // Дополнительная проверка через 2 секунды на случай медленной загрузки
    setTimeout(checkFavoritesOnLoad, 2000);
});

async function toggleFavorite(element, productId) {
    try {
        const response = await fetch(`/favorites/toggle/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const heartIcon = element.querySelector('.heart-icon');
            if (heartIcon) {
                heartIcon.classList.toggle('active');
            }

            // Если фильтр избранного активен - обновляем отображение
            const favoritesCheckbox = document.getElementById('favoritesOnlyCheckbox');
            if (favoritesCheckbox && favoritesCheckbox.checked) {
                processFavoritesFilter();
            }
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

function showAuthModal() {
    alert('Для добавления в избранное необходимо авторизоваться');
}