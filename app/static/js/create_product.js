// Отправка формы
document.getElementById('product-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('name').value,
        description: document.getElementById('description').value,
        price: parseInt(document.getElementById('price').value),
        image_url: document.getElementById('image_url').value,
        stock: parseInt(document.getElementById('stock').value),
        category_id: parseInt(document.getElementById('category_id').value)
    };
    
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

        const result = await response.json();
        
        if (response.ok) {
            showAlert('Товар успешно добавлен!', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            showAlert(result.detail || 'Ошибка при добавлении товара', 'error');
        }
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
        console.error('Ошибка:', error);
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