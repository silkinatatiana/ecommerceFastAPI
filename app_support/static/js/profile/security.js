async function sendPatchRequest(event) {
    event.preventDefault();

    const form = event.target;
    const formData = {
        old_password: form.old_password.value,
        new_password: form.new_password.value,
        new_password_one_more_time: form.confirm_password.value
    };

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Сохранение...';
    submitBtn.disabled = true;

    try {
        const response = await fetch(`/auth/update/password`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            alert('Пароль успешно изменен');
            form.reset();
            setTimeout(() => {
                toggleEditForm('password');
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }, 1000);
        } else {
            throw new Error(result.detail || 'Ошибка сервера');
        }
    } catch (error) {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        alert(error.message);
    }
}

document.getElementById('update-password-form')?.addEventListener('submit', sendPatchRequest);

async function deleteAccount() {
    if (!confirm("Вы уверены, что хотите удалить аккаунт? Это действие нельзя отменить.")) {
        return;
    }

    try {
        const response = await fetch('/auth/delete', {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            window.location.href = '/auth/create';
        } else {
            const errorText = await response.text();
            alert('Ошибка при удалении аккаунта: ' + errorText);
        }
    } catch (error) {
        console.error('Ошибка сети:', error);
        alert('Произошла ошибка при подключении к серверу.');
    }
}

