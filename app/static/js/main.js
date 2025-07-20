async function loadAllProducts(categoryId, button) {
    const skip = parseInt(button.dataset.skip);
    console.log(skip)
    const container = document.getElementById(`products-${categoryId}`);
    const mainGrid = button.closest('.category').querySelector('.products-grid');
    const hideBtn = button.parentElement.querySelector('.hide-btn');
    
    container.innerHTML = '<p>Загрузка...</p>';
    button.disabled = true;
    
    try {
        const response = await fetch(`/products/by_category/?categoryId=${categoryId}&skip=${skip}`);
        
        if (!response.ok) throw new Error(await response.text());
        
        const additionalProducts = await response.json();
        
        if (additionalProducts.length === 0) {
            container.innerHTML = '<p>Нет дополнительных товаров</p>';
            return;
        }

        additionalProducts.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card additional-product';
            productCard.dataset.category = categoryId;
            
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

// Закрываем фильтр при клике вне его области
document.addEventListener('click', function(event) {
    const filterContainer = document.querySelector('.category-filter');
    if (!filterContainer.contains(event.target)) {
        document.getElementById('categoryDropdown').style.display = 'none';
    }
});

// Обработка выбора категории
document.querySelectorAll('.filter-option').forEach(option => {
    option.addEventListener('click', function(e) {
        if (this.getAttribute('href') !== '#') {
            e.preventDefault();
            const url = this.getAttribute('href');
            window.history.pushState({}, '', url);
            location.reload();
        }
    });
});
