function showPasswordReset() {
    document.querySelectorAll('.auth-form').forEach(form => {
        form.style.display = 'none';
    });
    document.getElementById('password-reset-form').style.display = 'block';
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
    });
}

function switchTab(tabName) {
    // Переключение активной вкладки
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`.auth-tab[onclick="switchTab('${tabName}')"]`).classList.add('active');

    // Переключение активной формы
    document.querySelectorAll('.auth-form').forEach(form => {
        form.style.display = 'none';
    });

    // Показываем выбранную форму
    if (tabName === 'login') {
        document.getElementById('login-form').style.display = 'block';
    } else if (tabName === 'register') {
        document.getElementById('register-form').style.display = 'block';
    }

    // Скрываем все сообщения об ошибках
    document.querySelectorAll('.error-message, .success-message').forEach(msg => {
        msg.style.display = 'none';
    });
}

document.getElementById('register-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const errorElement = document.getElementById('register-error');
    const successElement = document.getElementById('success-message');

    errorElement.style.display = 'none';
    successElement.style.display = 'none';

    try {
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json' // Важно!
            },
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok) {
            if (result.redirect_url) {
                window.location.href = result.redirect_url;
            } else {
                successElement.textContent = 'Регистрация успешна!';
                successElement.style.display = 'block';
            }
        } else {
            errorElement.textContent = result.detail || 'Ошибка регистрации';
            errorElement.style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка:', error);
        errorElement.textContent = 'Произошла ошибка при отправке формы';
        errorElement.style.display = 'block';
    }
});