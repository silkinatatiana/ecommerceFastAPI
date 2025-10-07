document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('profile-edit-form').style.display = 'none';
    document.getElementById('password-edit-form').style.display = 'none';

    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

            this.classList.add('active');

            const sectionId = this.getAttribute('data-section') || this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(sectionId);

            if (targetSection) {
                targetSection.classList.add('active');
            }

            if (sectionId === 'orders') {
                updateUrlParameter('section', 'orders');
            }
        });
    });

    const urlParams = new URLSearchParams(window.location.search);
    const section = urlParams.get('section');
    const page = urlParams.get('page');

    if (section === 'orders') {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

        const ordersLink = document.querySelector('[data-section="orders"]');
        if (ordersLink) {
            ordersLink.classList.add('active');
        }
        document.getElementById('orders').classList.add('active');
    }
});

async function loadMoreOrders(userId, page) {
    try {
        const response = await fetch(`/orders/user/${userId}?page=${page}&per_page=5`);

        if (!response.ok) {
            throw new Error('Ошибка загрузки заказов');
        }

        const data = await response.json();
        const ordersContainer = document.getElementById('orders-container');
        const loadMoreContainer = document.querySelector('.load-more-container');

        if (data.orders && data.orders.length > 0) {
            data.orders.forEach(order => {
                const orderCard = createOrderCard(order);
                ordersContainer.insertBefore(orderCard, loadMoreContainer);
            });

            if (data.pagination && data.pagination.has_next) {
                document.getElementById('load-more-btn').setAttribute('onclick', `loadMoreOrders(${userId}, ${data.pagination.page + 1})`);
            } else {
                loadMoreContainer.style.display = 'none';
            }
        }

    } catch (error) {
        console.error('Ошибка при загрузке заказов:', error);
        alert('Произошла ошибка при загрузке заказов');
    }
}

function createOrderCard(order) {
    const card = document.createElement('div');
    card.className = 'order-card';

    const orderDate = new Date(order.date);
    const formattedDate = orderDate.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    card.innerHTML = `
        <div class="order-header">
            <h3>Заказ #${order.id}</h3>
            <span class="status ${order.status.toLowerCase()}">${order.status}</span>
        </div>
        <div class="order-details">
            <p>Дата: ${formattedDate}</p>
            <p>Сумма: ${order.summa} руб.</p>
            <p>Статус: ${order.status}</p>
        </div>
        <a href="/orders/order/${order.id}" class="btn btn-primary">Подробнее о заказе</a>
    `;

    return card;
}

function updateUrlParameter(key, value) {
    const url = new URL(window.location);
    url.searchParams.set(key, value);
    window.history.replaceState({}, '', url);
}

function toggleEditForm(type) {
    const form = document.getElementById(`${type}-edit-form`);
    if (form) {
        form.style.display = form.style.display === 'none' || form.style.display === '' ? 'block' : 'none';
    }
}

document.getElementById('update-profile-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/auth/update', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Успех:', result);
            alert('Профиль обновлен!');

            setTimeout(() => {
                window.location.reload();
            }, 1000);

        } else {
            console.error('Ошибка сервера:', response.status);
            alert('Произошла ошибка при обновлении профиля.');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Сетевая ошибка или сервер недоступен.');
    }
});
