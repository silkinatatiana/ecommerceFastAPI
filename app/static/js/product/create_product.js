document.addEventListener('DOMContentLoaded', function() {
    const productForm = document.getElementById('product-form');
    const alertContainer = document.getElementById('alert-container');

    productForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        try {
            const name = document.getElementById('name').value.trim();
            const price = parseFloat(document.getElementById('price').value);
            const stock = parseInt(document.getElementById('stock').value);
            const categoryId = document.getElementById('category_id').value;
            const fileInput = document.getElementById('files');

            const errors = [];
            if (!name) errors.push('Укажите название товара');
            if (isNaN(price) || price <= 0) errors.push('Укажите корректную цену');
            if (isNaN(stock) || stock < 0) errors.push('Укажите корректное количество');
            if (!categoryId) errors.push('Выберите категорию');
            if (!fileInput.files?.length) errors.push('Добавьте хотя бы одно изображение товара');

            if (errors.length > 0) {
                showAlert(errors.join('<br>'), 'error');
                return;
            }

            const formData = new FormData();
            formData.append('name', name);
            formData.append('description', document.getElementById('description').value.trim());
            formData.append('price', price);
            formData.append('stock', stock);
            formData.append('category_id', categoryId);
            formData.append('color', document.getElementById('color').value.trim());
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('files', fileInput.files[i]);
            }

            const laptopFields = document.getElementById('laptopFields');
            if (laptopFields && laptopFields.style.display === 'block') {
                const ram = document.getElementById('RAM_capacity')?.value?.trim();
                const mem = document.getElementById('built_in_memory_capacity')?.value?.trim();
                const screenVal = document.getElementById('screen')?.value;
                const cpu = document.getElementById('cpu')?.value?.trim();
                const cores = document.getElementById('number_of_processor_cores')?.value;
                const gpuCores = document.getElementById('number_of_graphics_cores')?.value;
                if (ram) formData.append('RAM_capacity', ram);
                if (mem) formData.append('built_in_memory_capacity', mem);
                if (screenVal) formData.append('screen', screenVal);
                if (cpu) formData.append('cpu', cpu);
                if (cores) formData.append('number_of_processor_cores', cores);
                if (gpuCores) formData.append('number_of_graphics_cores', gpuCores);
            }

            const response = await fetch('/products/create', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                const msg = Array.isArray(err.detail) ? err.detail.map(d => d.msg || JSON.stringify(d)).join(', ') : (err.detail || 'Ошибка сервера');
                throw new Error(msg);
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