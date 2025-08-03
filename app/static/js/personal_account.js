document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();

        // Удаляем активный класс у всех ссылок
        document.querySelectorAll('.nav-link').forEach(item => {
            item.classList.remove('active');
        });

        // Добавляем активный класс текущей ссылке
        this.classList.add('active');

        // Скрываем все разделы
        document.querySelectorAll('.account-main .section').forEach(section => {
            section.style.display = 'none';
        });

        // Показываем выбранный раздел
        const sectionId = this.getAttribute('href').substring(1);
        document.getElementById(sectionId).style.display = 'block';
    });
});

// Переключение форм редактирования
function toggleEditForm(formType) {
    const form = document.getElementById(`${formType}-edit-form`);
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

// Обработка форм
document.getElementById('update-profile-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);

    try {
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        });

        if (response.ok) {
            alert('Данные успешно обновлены!');
            location.reload();
        } else {
            const error = await response.json();
            alert(error.detail || 'Ошибка обновления данных');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при обновлении данных');
    }
});

document.getElementById('update-password-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    if (document.getElementById('new_password').value !==
        document.getElementById('confirm_password').value) {
        alert('Новый пароль и подтверждение не совпадают');
        return;
    }

    const formData = new FormData(this);

    try {
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'Accept': 'application/json'
            }
        });

        if (response.ok) {
            alert('Пароль успешно изменен!');
            toggleEditForm('password');
        } else {
            const error = await response.json();
            alert(error.detail || 'Ошибка изменения пароля');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при изменении пароля');
    }
});