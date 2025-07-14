document.addEventListener('DOMContentLoaded', function() {
    
    const form = document.getElementById('product-form');
    if (!form) {
        console.error('ОШИБКА: Форма не найдена. Добавьте id="product-form"');
        return;
    }

    const submitBtn = document.getElementById('submit-btn');
    if (!submitBtn) {
        console.error('ОШИБКА: Кнопка не найдена. Проверьте id="submit-btn"');
        return;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Начата отправка формы');
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
            
            const formData = new FormData(form);
            const data = {
                name: formData.get('name'),
                description: formData.get('description'),
                price: parseFloat(formData.get('price')),
                stock: parseInt(formData.get('stock')),
                category_id: parseInt(formData.get('category_id')),
                image_urls: Array.from(formData.getAll('image_urls[]'))
                           .filter(url => url.trim() !== '')
            };
            
            console.log('Отправляемые данные:', data);

            const response = await fetch('/products/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            console.log('Ответ сервера:', result);

            if (response.ok && result.id) {
                window.location.href = `/products/${result.id}`;
            } else {
                throw new Error(result.detail || 'Ошибка создания товара');
            }
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert(error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'ДОБАВИТЬ ТОВАР';
        }
    });
    
    const addImageBtn = document.getElementById('add-image-btn');
    if (addImageBtn) {
        addImageBtn.addEventListener('click', function() {
            const container = document.getElementById('image-inputs');
            if (container.querySelectorAll('input').length < 5) {
                const input = document.createElement('input');
                input.type = 'url';
                input.name = 'image_urls[]';
                input.required = true;
                input.placeholder = 'Ссылка на изображение';
                container.appendChild(input);
            }
        });
    }
});