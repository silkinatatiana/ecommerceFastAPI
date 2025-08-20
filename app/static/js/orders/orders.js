document.addEventListener('DOMContentLoaded', function() {
    const productsData = {{ products|tojson }};
    const productsList = document.getElementById('productsList');

    function renderProducts() {
        if (productsData && productsData.length > 0) {
            productsList.innerHTML = '';

            productsData.forEach(product => {
                const productElement = createProductElement(product);
                productsList.appendChild(productElement);
            });
        } else {
            productsList.innerHTML = '<p class="no-products">В заказе нет товаров</p>';
        }
    }

    function createProductElement(product) {
        const productDiv = document.createElement('div');
        productDiv.className = 'product-item';

        productDiv.innerHTML = `
            <img src="${product.image_url}" alt="${product.name}" class="product-image" onerror="this.src='/static/images/placeholder.jpg'">
            <div class="product-details">
                <h3 class="product-name">${product.name}</h3>
                <p class="product-price">Цена: ${product.price} руб.</p>
                <p class="product-quantity">Количество: ${product.count}</p>
                <p class="product-total">Сумма: ${product.item_total} руб.</p>
            </div>
        `;

        productDiv.addEventListener('click', function() {
            window.location.href = `/products/${product.id}`;
        });

        productDiv.style.cursor = 'pointer';

        return productDiv;
    }

    function formatDate(dateString) {
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('ru-RU', options);
    }

    const dateElement = document.querySelector('[data-date]');
    if (dateElement) {
        dateElement.textContent = formatDate(dateElement.dataset.date);
    }

    renderProducts();

    const backButton = document.getElementById('backButton');
    if (backButton) {
        backButton.addEventListener('click', function() {
            window.history.back();
        });
    }

    function checkOrderStatus() {

        const statusElement = document.querySelector('.order-status');
        if (statusElement) {
            const status = statusElement.textContent.trim().toLowerCase();

            if (status === 'processing') {
                console.log('Заказ в обработке...');
            }
        }
    }

    checkOrderStatus();

    document.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            e.target.src = '/static/images/placeholder.jpg';
        }
    }, true);
});