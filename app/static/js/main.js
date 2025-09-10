function applyFilters() {
    const params = new URLSearchParams();

    const categoryCheckboxes = document.querySelectorAll('input[name="category"]:checked');
    if (categoryCheckboxes.length > 0) {
        params.append('category_id', Array.from(categoryCheckboxes).map(cb => cb.value).join(','));
    }

    const colorCheckboxes = document.querySelectorAll('input[name="color"]:checked');
    if (colorCheckboxes.length > 0) {
        params.append('colors', Array.from(colorCheckboxes).map(cb => cb.value).join(','));
    }

    const memoryCheckboxes = document.querySelectorAll('input[name="built_in_memory"]:checked');
    if (memoryCheckboxes.length > 0) {
        params.append('built_in_memory', Array.from(memoryCheckboxes).map(cb => cb.value).join(','));
    }

    const favoritesCheckbox = document.getElementById('favoritesOnlyCheckbox');
    if (favoritesCheckbox && favoritesCheckbox.checked) {
        params.append('is_favorite', 'true');
    }

    window.location.search = params.toString();
}

function resetFilters() {
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    window.location.href = window.location.pathname;
}

function loadMoreProducts(categoryId, buttonElement) {
    let currentPage = parseInt(buttonElement.getAttribute('data-current-page')) || 1;
    let nextPage = currentPage + 1;

    const url = new URL(window.location.href);
    const searchParams = new URLSearchParams();

    const currentParams = new URLSearchParams(window.location.search);
    for (let [key, value] of currentParams) {
        if (key !== 'page' && !key.startsWith('page_cat_')) {
            searchParams.set(key, value);
        }
    }

    for (let [key, value] of currentParams) {
        if (key.startsWith('page_cat_') && key !== `page_cat_${categoryId}`) {
            searchParams.set(key, value);
        }
    }

    searchParams.set(`page_cat_${categoryId}`, nextPage);
    searchParams.set('partial', 'true');

    url.search = searchParams.toString();

    console.log("Запрос на URL:", url.toString());

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newProductsContainer = doc.querySelector(`[data-category-id="${categoryId}"] .products-grid`);

            if (newProductsContainer) {
                const productCards = newProductsContainer.querySelectorAll('.product-card');

                if (productCards.length > 0) {
                    const currentGrid = document.querySelector(`[data-category-id="${categoryId}"] .products-grid`);
                    currentGrid.insertAdjacentHTML('beforeend', newProductsContainer.innerHTML);

                    // Обновляем текущую страницу кнопки
                    buttonElement.setAttribute('data-current-page', nextPage);

                    // ✅ ВАЖНО: определяем, есть ли еще товары
                    // Для этого ищем в ответе кнопку "Показать еще" — если она есть, значит, есть еще страницы
                    const nextLoadMoreBtnInResponse = doc.querySelector(`.load-more-btn[data-category-id="${categoryId}"]`);
                    const hasMore = !!nextLoadMoreBtnInResponse;

                    updateButtonVisibility(categoryId, nextPage, hasMore);
                } else {
                    // Если новых товаров нет — скрываем кнопку
                    updateButtonVisibility(categoryId, nextPage, false);
                }
            } else {
                // Если контейнер не найден — тоже скрываем кнопку
                updateButtonVisibility(categoryId, nextPage, false);
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке товаров:', error);
            alert('Не удалось загрузить товары. Попробуйте позже.');
        });
}

function updateButtonVisibility(categoryId, currentPage, hasMore) {
    const loadMoreBtn = document.querySelector(`.load-more-btn[data-category-id="${categoryId}"]`);
    const collapseBtn = document.querySelector(`.collapse-btn[data-category-id="${categoryId}"]`);

    if (loadMoreBtn) {
        loadMoreBtn.style.display = hasMore ? 'inline-block' : 'none';
    }

    if (collapseBtn) {
        collapseBtn.style.display = (currentPage > 1) ? 'inline-block' : 'none';
    }
}

function collapseProducts(categoryId, buttonElement) {
    const grid = document.querySelector(`[data-category-id="${categoryId}"] .products-grid`);
    if (grid) {
        const cards = grid.querySelectorAll('.product-card');
        for (let i = 3; i < cards.length; i++) {
            cards[i].remove();
        }
    }

    const loadMoreBtn = document.querySelector(`.load-more-btn[data-category-id="${categoryId}"]`);
    if (loadMoreBtn) {
        loadMoreBtn.setAttribute('data-current-page', 1);
        loadMoreBtn.style.display = 'inline-block';
    }

    buttonElement.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.category').forEach(category => {
        const categoryId = category.dataset.categoryId;
        const loadMoreBtn = category.querySelector('.load-more-btn');

        if (loadMoreBtn) {
            const currentPage = parseInt(loadMoreBtn.dataset.currentPage || 1);
            const hasMore = loadMoreBtn.style.display !== 'none';
            updateButtonVisibility(categoryId, currentPage, hasMore);
        }
    });

    initFiltersFromUrl();

    checkFavoritesOnLoad();
});

function initFiltersFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);

    const categoryParam = urlParams.get('category_id');
    if (categoryParam) {
        const categories = categoryParam.split(',');
        categories.forEach(cat => {
            const checkbox = document.querySelector(`input[name="category"][value="${cat}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    const favoritesOnly = urlParams.get('is_favorite');
    if (favoritesOnly === 'true') {
        const checkbox = document.getElementById('favoritesOnlyCheckbox');
        if (checkbox) checkbox.checked = true;
    }

    const colorParam = urlParams.get('colors');
    if (colorParam) {
        const colors = colorParam.split(',');
        colors.forEach(color => {
            const checkbox = document.querySelector(`input[name="color"][value="${color}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    const memoryParam = urlParams.get('built_in_memory');
    if (memoryParam) {
        const memories = memoryParam.split(',');
        memories.forEach(mem => {
            const checkbox = document.querySelector(`input[name="built_in_memory"][value="${mem}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

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
        showAllContent();
        return;
    }

    const favoriteProducts = document.querySelectorAll('.product-card .heart-icon.active');
    const hasFavorites = favoriteProducts.length > 0;

    if (hasFavorites) {
        showOnlyFavorites();
    } else {
        showNoFavoritesMessage();
    }
}

function showAllContent() {
    const categories = document.querySelectorAll('.category');
    categories.forEach(category => {
        category.style.display = 'block';
    });

    const products = document.querySelectorAll('.product-card');
    products.forEach(product => {
        product.style.display = 'block';
    });

    const urlParams = new URLSearchParams(window.location.search);
    const hasActiveFilters = urlParams.get('is_favorite') === 'true' ||
                           urlParams.get('colors') ||
                           urlParams.get('built_in_memory');

    if (hasActiveFilters) {
        hideCategoryTitles();
    } else {
        showCategoryTitles();
    }

    const noFavoritesMessage = document.querySelector('.no-favorites-message');
    if (noFavoritesMessage) {
        noFavoritesMessage.remove();
    }
}

function showOnlyFavorites() {
    const categories = document.querySelectorAll('.category');
    let hasVisibleCategories = false;

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

    const noFavoritesMessage = document.querySelector('.no-favorites-message');
    if (noFavoritesMessage) {
        noFavoritesMessage.remove();
    }

    if (!hasVisibleCategories) {
        showNoFavoritesMessage();
    }
}

function showNoFavoritesMessage() {
    const categories = document.querySelectorAll('.category');
    categories.forEach(category => {
        category.style.display = 'none';
    });

    const existingMessage = document.querySelector('.no-favorites-message');
    if (existingMessage) {
        return;
    }

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

function checkFavoritesOnLoad() {
    const urlParams = new URLSearchParams(window.location.search);
    const isFavoriteFilterActive = urlParams.get('is_favorite') === 'true';

    const hasActiveFilters = isFavoriteFilterActive ||
                           urlParams.get('colors') ||
                           urlParams.get('built_in_memory');

    if (hasActiveFilters) {
        hideCategoryTitles();
    }

    if (isFavoriteFilterActive) {
        setTimeout(() => {
            processFavoritesFilter();
        }, 1000);
    }
}

function showAuthModal() {
    alert('Для добавления в избранное необходимо авторизоваться');
}