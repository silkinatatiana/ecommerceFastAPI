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

function redirectToHome() {
    window.location.href = '/';
}

document.getElementById('register-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const errorElement = document.getElementById('register-error');
    const successElement = document.getElementById('success-message');

    const data = {
        first_name: document.getElementById('register-first_name').value,
        last_name: document.getElementById('register-last_name').value,
        username: document.getElementById('register-username').value,
        email: document.getElementById('register-email').value,
        password: document.getElementById('register-password').value,
        confirm_password: document.getElementById('register-confirm-password').value,
        role: document.getElementById('register-role').value
    };

    if (data.password !== data.confirm_password) {
        errorElement.textContent = 'Пароли не совпадают';
        errorElement.style.display = 'block';
        successElement.style.display = 'none';
        return;
    }

    errorElement.style.display = 'none';
    successElement.style.display = 'none';

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        if (response.status === 303 || response.redirected) {
            const redirectUrl = response.headers.get('Location') || response.url;
            window.location.href = redirectUrl;
            return;
        }

        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            errorElement.textContent = result.detail || 'Ошибка регистрации';
            errorElement.style.display = 'block';
            return;
        }

        redirectToHome();

    } catch (error) {
        console.error('Ошибка при регистрации:', error);
        errorElement.textContent = 'Не удалось отправить запрос. Проверьте соединение.';
        errorElement.style.display = 'block';
    }
});

document.getElementById('login-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const errorElement = document.getElementById('login-error');
    const successElement = document.getElementById('success-message');

    const data = {
        username: document.getElementById('login-username').value,
        password: document.getElementById('login-password').value
    };

    errorElement.style.display = 'none';
    successElement.style.display = 'none';

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        if (response.status === 303 || response.redirected) {
            const redirectUrl = response.headers.get('Location') || response.url;
            window.location.href = redirectUrl;
            return;
        }

        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            errorElement.textContent = result.detail || 'Ошибка входа';
            errorElement.style.display = 'block';
            return;
        }

        redirectToHome();

    } catch (error) {
        console.error('Ошибка при входе:', error);
        errorElement.textContent = 'Не удалось войти. Проверьте соединение.';
        errorElement.style.display = 'block';
    }
});