function toggleClientInfo(event) {
    event.preventDefault();
    const popup = document.getElementById('client-info-popup');
    popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
}

function closeClientInfo() {
    document.getElementById('client-info-popup').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.messages-area');
    container.scrollTop = container.scrollHeight;
});