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

async function submitAuthForm(form, isRegistration = false) {
    const errorElement = isRegistration
        ? document.getElementById('register-error')
        : document.getElementById('login-error');
    const successElement = document.getElementById('success-message');

    errorElement.style.display = 'none';
    successElement.style.display = 'none';

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    if (isRegistration && data.password !== data.confirm_password) {
        errorElement.textContent = 'Пароли не совпадают';
        errorElement.style.display = 'block';
        return;
    }

    try {
        const response = await fetch(form.action || (isRegistration ? '/auth/register' : '/auth/login'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        let result = {};
        try {
            result = await response.json();
        } catch (e) {
        }

        if (response.ok) {
            window.location.href = '/';
        } else {
            const errorMsg = result.detail || (isRegistration ? 'Ошибка регистрации' : 'Ошибка входа');
            errorElement.textContent = errorMsg;
            errorElement.style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка сети:', error);
        errorElement.textContent = 'Не удалось подключиться к серверу. Проверьте соединение.';
        errorElement.style.display = 'block';
    }
}

document.getElementById('register-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    await submitAuthForm(this, true);
});

document.getElementById('login-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    await submitAuthForm(this, false);
});