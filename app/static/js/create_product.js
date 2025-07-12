document.getElementById('product-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Собираем данные формы с проверкой
    const formData = {
        name: document.getElementById('name').value.trim(),
        description: document.getElementById('description').value.trim(),
        price: parseFloat(document.getElementById('price').value),
        image_url: document.getElementById('image_url').value.trim(),
        stock: parseInt(document.getElementById('stock').value),
        category_id: parseInt(document.getElementById('category_id').value)
    };

    // Валидация данных перед отправкой
    if (!formData.name || !formData.price || !formData.image_url || !formData.category_id) {
        showAlert('Пожалуйста, заполните все обязательные поля', 'error');
        return;
    }

    console.log('Отправляемые данные:', formData); // Логируем данные перед отправкой
    
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Отправка...';
    
    try {
        const response = await fetch('/products/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        console.log('Статус ответа:', response.status); // Логируем статус ответа
        
        // Сначала получаем текст ответа
        const responseText = await response.text();
        console.log('Полный ответ сервера:', responseText); // Логируем сырой ответ
        
        let result;
        try {
            // Пытаемся распарсить JSON
            result = JSON.parse(responseText);
        } catch (e) {
            // Если не удалось распарсить - значит сервер вернул не JSON
            console.error('Ошибка парсинга JSON:', e);
            throw new Error(`Сервер вернул невалидный JSON: ${responseText.slice(0, 100)}...`);
        }

        if (response.ok) {
            showAlert('Товар успешно добавлен!', 'success');
            console.log('Успешный ответ:', result);
            const productId = result.id

            if (productId) {
                // Перенаправляем на страницу товара через 1.5 секунды
                setTimeout(() => {
                    window.location.href = `/products/${productId}`;
                }, 1500);
        } else {
            const errorMsg = result.detail || result.message || 'Неизвестная ошибка сервера';
            showAlert(`Ошибка: ${errorMsg}`, 'error');
            console.error('Ошибка сервера:', result);
        }
    }
    } catch (error) {
        console.error('Ошибка запроса:', error);
        showAlert(`Ошибка: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Добавить товар';
    }
});

function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alertContainer.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}