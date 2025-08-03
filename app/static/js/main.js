async function loadAllProducts(categoryId, button) {
    const skip = parseInt(button.dataset.skip);
    const container = document.getElementById(`products-${Array.isArray(categoryId) ? categoryId[0] : categoryId}`);
    const mainGrid = button.closest('.category').querySelector('.products-grid');
    const hideBtn = button.parentElement.querySelector('.hide-btn');

    container.innerHTML = '<p>Загрузка...</p>';
    button.disabled = true;

    try {
        const params = new URLSearchParams();
        if (Array.isArray(categoryId)) {
            categoryId.forEach(id => params.append('categoryId', id));
        } else {
            params.append('categoryId', categoryId);
        }
        params.append('skip', skip);

        const response = await fetch(`/products/by_category/?${params.toString()}`);

        if (!response.ok) throw new Error(await response.text());

        const additionalProducts = await response.json();

        if (additionalProducts.length === 0) {
            container.innerHTML = '<p>Нет дополнительных товаров</p>';
            return;
        }

        additionalProducts.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card additional-product';
            productCard.dataset.category = product.category_id;

            productCard.innerHTML = `
                <img src="${product.image_urls?.[0] || '/static/images/default_image.png'}"
                    alt="${product.name}"
                    loading="lazy"
                    onerror="this.onerror=null;this.src='/static/images/default_image.png'">
                <h3>${product.name}</h3>
                <p class="product-price">${product.price || 'Цена не указана'} ₽</p>
                <p class="product-stock ${product.stock <= 0 ? 'out-of-stock' : ''}">
                    ${product.stock} шт. в наличии
                </p>
            `;

            productCard.addEventListener('click', () => {
                window.location.href = `/products/${product.id}`;
            });

            mainGrid.appendChild(productCard);
        });

        button.dataset.skip = skip + additionalProducts.length;

        hideBtn.style.display = 'inline-block';

        if (additionalProducts.length < 6) {
            button.style.display = 'none';
        }

    } catch (error) {
        container.innerHTML = `<p>Ошибка загрузки: ${error.message}</p>`;
        console.error('Ошибка:', error);
    } finally {
        button.disabled = false;
        container.innerHTML = '';
    }
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

//// Закрываем фильтр при клике вне его области
//document.addEventListener('click', function(event) {
//    const filterContainer = document.querySelector('.category-filter');
//    if (!filterContainer.contains(event.target)) {
//        document.getElementById('categoryDropdown').style.display = 'none';
//    }
//});

document.querySelectorAll('input[name="category"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        // 1. Собираем все выбранные категории
        const selectedCategories = Array.from(
            document.querySelectorAll('input[name="category"]:checked')
        ).map(el => el.value).join(',');

        // 2. Собираем выбранную память
        const selectedMemory = Array.from(
            document.querySelectorAll('input[name="built_in_memory"]:checked')
        ).map(el => el.value).join(',');

        // 3. Формируем URL
        const params = new URLSearchParams();
        if (selectedCategories.length > 0) {
            params.append('categoryId', selectedCategories.join(','));
        }
        if (selectedMemory) {
            params.append('built_in_memory', selectedMemory);
        }

        // 4. Обновляем URL без перезагрузки
        const url = params.toString()
            ? `/products?${params.toString()}`
            : '/products';
        window.history.pushState({}, '', url);

        // 5. Загружаем товары
        loadFilteredProducts(selectedCategories);
    });
});

async function loadFilteredProducts(categoryId) {
    try {
        const params = new URLSearchParams();
        if (categoryId.length > 0) {
            params.append('category_id', categoryId.join(','));
        }

        // Добавьте другие параметры фильтрации, если нужно

        const response = await fetch(`/products?${params.toString()}`);
        if (!response.ok) throw new Error(await response.text());

        return await response.json();
    } catch (error) {
        console.error('Ошибка загрузки продуктов:', error);
        return [];
    }
}

function getSelectedCategoryId() {
    return Array.from(document.querySelectorAll('.filter-option.selected'))
               .map(opt => opt.dataset.categoryId);
}

function initFiltersFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const memoryParam = urlParams.get('built_in_memory');

    // Категории
    const categoryParam = urlParams.get('category_id');
    if (categoryParam) {
        const categories = categoryParam.split(',');
        categories.forEach(cat => {
            const checkbox = document.querySelector(`input[name="category"][value="${cat}"]`);
            if (checkbox) checkbox.checked = true;
        });
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

    if (memoryParam) {
    const memories = memoryParam.split(',');
    memories.forEach(mem => {
        const checkbox = document.querySelector(`input[name="built_in_memory"][value="${mem}"]`);
        if (checkbox) checkbox.checked = true;
    });
}
}

document.addEventListener('DOMContentLoaded', initFiltersFromUrl);

function applyFilters() {
            const selectedCategories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
                .map(el => el.value)
                .join(',');

            const selectedColors = Array.from(document.querySelectorAll('input[name="color"]:checked'))
                .map(el => el.value)
                .join(',');

            const selectedMemory = Array.from(document.querySelectorAll('input[name="built_in_memory"]:checked'))
                .map(el => el.value)
                .join(',');

            const params = new URLSearchParams();

            if (selectedCategories) params.append('category_id', selectedCategories);
            if (selectedColors) params.append('colors', selectedColors);
            if (selectedMemory) params.append('built_in_memory', selectedMemory);

            window.location.search = params.toString();
        }

        function resetFilters() {
            window.location.search = '';
        }

        // Инициализация фильтров из URL
        document.addEventListener('DOMContentLoaded', function() {
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

        });

document.addEventListener('DOMContentLoaded', function() {
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



