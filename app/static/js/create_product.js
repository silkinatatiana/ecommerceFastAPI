document.addEventListener('DOMContentLoaded', function() {
    const productForm = document.getElementById('product-form');
    const alertContainer = document.getElementById('alert-container');

    productForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        try {
            // Основные данные
            const formData = {
                name: document.getElementById('name').value.trim(),
                description: document.getElementById('description').value.trim() || null,
                price: parseInt(document.getElementById('price').value),
                stock: parseInt(document.getElementById('stock').value),
                category_id: parseInt(document.getElementById('category_id').value),
                image_urls: Array.from(document.querySelectorAll('input[name="image_urls[]"]'))
                    .map(input => input.value.trim())
                    .filter(url => url.length > 0),
                color: document.getElementById('color').value.trim() || null
            };

            // Технические характеристики (если это ноутбук)
            const laptopFieldsSection = document.getElementById('laptopFields');
            if (laptopFieldsSection.style.display === 'block') {
                formData.RAM_capacity = document.getElementById('RAM_capacity').value.trim() || null;
                formData.built_in_memory_capacity = document.getElementById('built_in_memory_capacity').value.trim() || null;
                
                const screenValue = document.getElementById('screen').value;
                formData.screen = screenValue ? parseFloat(screenValue) : null;
                
                formData.cpu = document.getElementById('cpu').value.trim() || null;
                
                const coresValue = document.getElementById('number_of_processor_cores').value;
                formData.number_of_processor_cores = coresValue ? parseInt(coresValue) : null;
                
                const graphicsValue = document.getElementById('number_of_graphics_cores').value;
                formData.number_of_graphics_cores = graphicsValue ? parseInt(graphicsValue) : null;
            }

            // Валидация
            const errors = [];
            if (!formData.name) errors.push('Название товара обязательно');
            if (isNaN(formData.price) || formData.price <= 0) errors.push('Укажите корректную цену (целое число больше 0)');
            if (isNaN(formData.stock) || formData.stock < 0) errors.push('Количество не может быть отрицательным');
            if (!formData.image_urls || formData.image_urls.length === 0) errors.push('Добавьте хотя бы одно изображение');
            if (isNaN(formData.category_id)) errors.push('Выберите категорию');

            if (errors.length > 0) {
                showAlert(errors.join('<br>'), 'error');
                return;
            }

            // Отправка данных
            const response = await fetch('/products/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const responseData = await response.json();
            
            if (!response.ok) {
                // Обработка ошибок валидации FastAPI
                if (response.status === 422 && responseData.detail) {
                    const errorDetails = Array.isArray(responseData.detail) 
                        ? responseData.detail.map(err => `${err.loc[1]}: ${err.msg}`).join('<br>')
                        : responseData.detail;
                    throw new Error(errorDetails);
                }
                throw new Error(responseData.detail || 'Ошибка сервера');
            }

            showAlert('Товар успешно создан!', 'success');
            setTimeout(() => {
                window.location.href = `/products/${responseData.id}`;
            }, 1500);

        } catch (error) {
            console.error('Ошибка:', error);
            showAlert(error.message || 'Произошла ошибка при создании товара', 'error');
        }
    });

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

    // Показ/скрытие полей для ноутбуков
    const categorySelect = document.getElementById('category_id');
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            const laptopFieldsSection = document.getElementById('laptopFields');
            if (laptopFieldsSection) {
                const selectedOption = this.options[this.selectedIndex].text.toLowerCase();
                const isLaptop = selectedOption.includes('ноутбук') || selectedOption.includes('laptop');
                laptopFieldsSection.style.display = isLaptop ? 'block' : 'none';
            }
        });
    }
});