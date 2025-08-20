document.addEventListener('DOMContentLoaded', function() {
    console.log('Script loaded'); // Отладочное сообщение

    // 1. Добавление изображений
    const MAX_IMAGES = 5;
    const addImageBtn = document.getElementById('add-image-btn');
    const imagesContainer = document.getElementById('image-inputs');

    addImageBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const inputs = document.querySelectorAll('#image-inputs input[type="url"]');
        if (inputs.length >= MAX_IMAGES) {
            alert(`Максимум ${MAX_IMAGES} изображений`);
            return;
        }

        const newInput = document.createElement('input');
        newInput.type = 'url';
        newInput.name = 'image_urls[]';
        newInput.className = 'form-control';
        newInput.placeholder = `https://example.com/image${inputs.length + 1}.jpg`;
        newInput.required = inputs.length === 0;

        const container = document.createElement('div');
        container.className = 'image-input-container';
        container.appendChild(newInput);

        if (inputs.length > 0) {
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-image-btn';
            removeBtn.textContent = '×';
            removeBtn.addEventListener('click', function() {
                container.remove();
                addImageBtn.disabled = false;
            });
            container.appendChild(removeBtn);
        }

        imagesContainer.appendChild(container);

        if (inputs.length + 1 >= MAX_IMAGES) {
            addImageBtn.disabled = true;
        }
    });

    // 2. Отправка формы
    const productForm = document.getElementById('product-form');
    const alertContainer = document.getElementById('alert-container');

    productForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submitted'); // Отладочное сообщение

        try {
            // Собираем данные формы
            const formData = {
                name: document.getElementById('name').value.trim(),
                description: document.getElementById('description').value.trim() || null,
                price: parseFloat(document.getElementById('price').value),
                stock: parseInt(document.getElementById('stock').value),
                category_id: parseInt(document.getElementById('category_id').value),
                supplier_id: parseInt(document.getElementById('supplier_id').value),
                image_urls: Array.from(document.querySelectorAll('input[name="image_urls[]"]'))
                    .map(input => input.value.trim())
                    .filter(url => url),
                color: document.getElementById('color').value.trim() || null
            };

            // Проверяем технические характеристики (для ноутбуков)
            const laptopFields = document.getElementById('laptopFields');
            if (laptopFields.style.display === 'block') {
                formData.RAM_capacity = document.getElementById('RAM_capacity').value.trim() || null;
                formData.built_in_memory_capacity = document.getElementById('built_in_memory_capacity').value.trim() || null;
                formData.screen = document.getElementById('screen').value ? parseFloat(document.getElementById('screen').value) : null;
                formData.cpu = document.getElementById('cpu').value.trim() || null;
                formData.number_of_processor_cores = document.getElementById('number_of_processor_cores').value ? parseInt(document.getElementById('number_of_processor_cores').value) : null;
                formData.number_of_graphics_cores = document.getElementById('number_of_graphics_cores').value ? parseInt(document.getElementById('number_of_graphics_cores').value) : null;
            }

            // Валидация
            const errors = [];
            if (!formData.name) errors.push('Укажите название товара');
            if (isNaN(formData.price) || formData.price <= 0) errors.push('Укажите корректную цену');
            if (isNaN(formData.stock) || formData.stock < 0) errors.push('Укажите корректное количество');
            if (isNaN(formData.category_id)) errors.push('Выберите категорию');
            if (formData.image_urls.length === 0) errors.push('Добавьте хотя бы одно изображение');

            if (errors.length > 0) {
                showAlert(errors.join('<br>'), 'error');
                return;
            }

            // Отправка на сервер
            console.log('Sending data:', formData); // Отладочное сообщение
            const response = await fetch('/products/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка сервера');
            }

            const result = await response.json();
            showAlert('Товар успешно создан!', 'success');
            setTimeout(() => {
                window.location.href = `/products/${result.id}`;
            }, 1500);

        } catch (error) {
            console.error('Error:', error);
            showAlert(error.message || 'Ошибка при создании товара', 'error');
        }
    });

    // 3. Показ/скрытие полей для ноутбуков
    const categorySelect = document.getElementById('category_id');
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            const laptopFields = document.getElementById('laptopFields');
            if (laptopFields) {
                const selectedText = this.options[this.selectedIndex].text.toLowerCase();
                laptopFields.style.display = (selectedText.includes('ноутбук') || selectedText.includes('laptop')) 
                    ? 'block' 
                    : 'none';
            }
        });
    }

    // Вспомогательная функция
    function showAlert(message, type = 'info') {
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