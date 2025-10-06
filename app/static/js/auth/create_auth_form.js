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
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`.auth-tab[onclick="switchTab('${tabName}')"]`).classList.add('active');

    document.querySelectorAll('.auth-form').forEach(form => {
        form.style.display = 'none';
    });

    if (tabName === 'login') {
        document.getElementById('login-form').style.display = 'block';
    } else if (tabName === 'register') {
        document.getElementById('register-form').style.display = 'block';
    }

    document.querySelectorAll('.error-message, .success-message').forEach(msg => {
        msg.style.display = 'none';
    });
}

document.getElementById('register-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const form = this;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    if (data.password !== data.confirm_password) {
        const errorElement = document.getElementById('register-error');
        errorElement.textContent = 'Пароли не совпадают';
        errorElement.style.display = 'block';
        return;
    }

    const errorElement = document.getElementById('register-error');
    const successElement = document.getElementById('success-message');

    errorElement.style.display = 'none';
    successElement.style.display = 'none';

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data),
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