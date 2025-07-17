async function loadAllProducts(categoryId, button) {
    const skip = parseInt(button.dataset.skip);
    const container = document.getElementById(`products-${categoryId}`);
    const mainGrid = button.closest('.category').querySelector('.products-grid');
    const hideBtn = button.parentElement.querySelector('.hide-btn'); // Находим кнопку "Скрыть"
    
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
        
        // Добавляем класс для новых товаров
        additionalProducts.forEach(product => {
            const productHtml = `
                <div class="product-card additional-product" data-category="${categoryId}">
                    <img src="${product.image_urls?.[0] || '/static/images/default_image.png'}" 
                         alt="${product.name}"
                         loading="lazy"
                         onerror="this.onerror=null;this.src='/static/images/default_image.png'">
                    <h3>${product.name}</h3>
                    <p class="product-price">${product.price || 'Цена не указана'} ₽</p>
                    <p class="product-stock ${product.stock <= 0 ? 'out-of-stock' : ''}">
                        ${product.stock} шт. в наличии
                    </p>
                </div>
            `;
            mainGrid.insertAdjacentHTML('beforeend', productHtml);
        });
        
        // Обновляем skip
        button.dataset.skip = skip + additionalProducts.length;
        
        // Показываем кнопку "Скрыть"
        hideBtn.style.display = 'inline-block';
        
        // Скрываем кнопку если больше нет товаров
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

// Новая функция для скрытия товаров (добавьте её в тот же файл)
function hideProducts(categoryId, button) {
    const viewAllBtn = button.parentElement.querySelector('.view-all-btn');
    const mainGrid = button.closest('.category').querySelector('.products-grid');
    
    // Удаляем только добавленные товары
    const additionalProducts = mainGrid.querySelectorAll(`.additional-product[data-category="${categoryId}"]`);
    additionalProducts.forEach(product => product.remove());
    
    // Восстанавливаем кнопку "Посмотреть все"
    viewAllBtn.style.display = 'inline-block';
    viewAllBtn.dataset.skip = 6; // Сбрасываем счётчик
    
    // Скрываем кнопку "Скрыть"
    button.style.display = 'none';
}