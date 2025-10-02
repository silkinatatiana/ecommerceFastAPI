function applyFilters() {
    const url = new URL(window.location);
    const pageParams = new URLSearchParams();
    for (const [key, value] of url.searchParams) {
        if (key.startsWith('page_cat_')) {
            pageParams.append(key, value);
        }
    }

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

    for (const [key, value] of pageParams) {
        params.append(key, value);
    }

    const newUrl = `${url.pathname}?${params.toString()}`;
    window.location.href = newUrl;
}

function resetFilters() {
    window.location.href = '/';
}

function loadMoreProducts(categoryId, button) {
    const currentPage = parseInt(button.dataset.currentPage);
    const nextPage = currentPage + 1;

    const url = new URL(window.location);
    url.searchParams.set(`page_cat_${categoryId}`, nextPage);
    url.searchParams.set('partial', 'true');
    url.searchParams.set('category_id', categoryId);

    fetch(url.toString())
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.text();
        })
        .then(html => {
            const container = document.querySelector(`.category[data-category-id="${categoryId}"]`);
            if (!container) return;

            const grid = container.querySelector('.products-grid');
            const actions = container.querySelector('.category-actions');

            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html.trim();

            const newGrid = tempDiv.querySelector('.products-grid');
            const newActions = tempDiv.querySelector('.category-actions');

            if (newGrid && grid) {
                grid.insertAdjacentHTML('beforeend', newGrid.innerHTML);
            }
            if (newActions && actions) {
                actions.innerHTML = newActions.innerHTML;
                const newButton = newActions.querySelector('button[data-category-id]');
                if (newButton) {
                    newButton.dataset.currentPage = nextPage;
                }
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке товаров:', error);
            alert('Не удалось загрузить больше товаров');
        });
}

function collapseProducts(categoryId, buttonElement) {
    const url = new URL(window.location);
    url.searchParams.delete(`page_cat_${categoryId}`);
    window.location.href = url.toString();
}

function initFiltersFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);

    const categoryParam = urlParams.get('category_id');
    if (categoryParam) {
        categoryParam.split(',').forEach(cat => {
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
        colorParam.split(',').forEach(color => {
            const checkbox = document.querySelector(`input[name="color"][value="${color}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    const memoryParam = urlParams.get('built_in_memory');
    if (memoryParam) {
        memoryParam.split(',').forEach(mem => {
            const checkbox = document.querySelector(`input[name="built_in_memory"][value="${mem}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }
}

function hideCategoryTitles() {
    document.querySelectorAll('.category h3').forEach(title => {
        title.style.display = 'none';
    });
}

function showCategoryTitles() {
    document.querySelectorAll('.category h3').forEach(title => {
        title.style.display = 'block';
    });
}

document.addEventListener('DOMContentLoaded', function () {
    initFiltersFromUrl();

    const urlParams = new URLSearchParams(window.location.search);
    let hasActiveFilters = false;
    for (const [key] of urlParams) {
        if (!key.startsWith('page_cat_')) {
            hasActiveFilters = true;
            break;
        }
    }
    if (hasActiveFilters) {
        hideCategoryTitles();
    }
});