document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();

        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

        this.classList.add('active');

        const sectionId = this.getAttribute('data-section');
        document.getElementById(sectionId).classList.add('active');

        if (sectionId === 'orders') {
            updateUrlParameter('page', 1);
        }
    });
});

async function loadMoreOrders(page) {
    try {
        const response = await fetch(`/api/user/{{ user.id }}?page=${page}&per_page=5`);
        if (!response.ok) {
            throw new Error('Ошибка загрузки заказов');
        }

        const data = await response.json();

        const ordersContainer = document.getElementById('orders-container');
        const loadMoreContainer = document.querySelector('.load-more-container');

        data.orders.forEach(order => {
            const orderCard = createOrderCard(order);
            ordersContainer.insertBefore(orderCard, loadMoreContainer);
        });

        if (data.pagination.has_next) {
            document.getElementById('load-more-btn').setAttribute('onclick', `loadMoreOrders(${page + 1})`);
        } else {
            loadMoreContainer.style.display = 'none';
        }

        updateUrlParameter('page', page);

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
    form.style.display = form.style.display === 'none' || form.style.display === '' ? 'block' : 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page');

    if (page && page > 1) {
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

        document.querySelector('[data-section="orders"]').classList.add('active');
        document.getElementById('orders').classList.add('active');
    }

    document.getElementById('profile-edit-form').style.display = 'none';
    document.getElementById('password-edit-form').style.display = 'none';
});