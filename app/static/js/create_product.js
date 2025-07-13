document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('product-form');
    const alertContainer = document.getElementById('alert-container');
    const imageInputsContainer = document.getElementById('image-inputs');
    const addImageBtn = document.getElementById('add-image-btn');

    // Добавление новых полей для изображений (максимум 5)
    addImageBtn.addEventListener('click', function() {
        const inputs = imageInputsContainer.querySelectorAll('input');
        if (inputs.length < 5) {
            const newInput = document.createElement('input');
            newInput.type = 'url';
            newInput.name = 'image_urls[]';
            newInput.placeholder = `https://example.com/image${inputs.length + 1}.jpg`;
            newInput.required = true;
            imageInputsContainer.appendChild(newInput);
        } else {
            showAlert('Максимум 5 изображений', 'warning');
        }
    });

    // Отправка формы
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;

        try {
            const formData = new FormData(form);
            const data = {
                name: formData.get('name'),
                description: formData.get('description'),
                price: parseFloat(formData.get('price')),
                stock: parseInt(formData.get('stock')),
                category_id: parseInt(formData.get('category_id')),
                image_urls: formData.getAll('image_urls[]')  // Получаем массив URL
            };

            const response = await fetch('/products/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showAlert('Товар успешно добавлен!', 'success');
                form.reset();
                // Очищаем добавленные поля изображений (оставляя только первое)
                const inputs = imageInputsContainer.querySelectorAll('input');
                inputs.forEach((input, index) => {
                    if (index > 0) input.remove();
                });
            } else {
                const error = await response.json();
                showAlert(error.detail || 'Ошибка при добавлении товара', 'error');
            }
        } catch (err) {
            showAlert('Ошибка сети или сервера', 'error');
        } finally {
            submitBtn.disabled = false;
        }
    });

    // Функция для показа уведомлений
    function showAlert(message, type) {
        alertContainer.innerHTML = `
            <div class="alert alert-${type}">
                ${message}
            </div>
        `;
        setTimeout(() => {
            alertContainer.innerHTML = '';
        }, 5000);
    }
});