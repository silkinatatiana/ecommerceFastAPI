function openUserModal(userId) {
    document.getElementById('userModal').style.display = 'block';
}

function closeUserModal() {
    document.getElementById('userModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('userModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};

function updateOrderStatus(orderId) {
    const select = document.getElementById('order-status');
    const new_status = select.value;

    fetch(`/support/change_status/${orderId}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_status: new_status })
    })
    .then(response => {
        if (response.ok) {
            alert('Статус успешно обновлён');
            window.location.reload();
        } else {
            alert('Ошибка при обновлении статуса');
        }
    })
    .catch(err => {
        console.error('Ошибка:', err);
        alert('Произошла ошибка при обновлении');
    });
}