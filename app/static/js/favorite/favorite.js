async function toggleFavorite(element, productId) {
    try {
        const response = await fetch(`/favorites/toggle/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const heartIcon = element.querySelector('.heart-icon');
            if (heartIcon) {
                heartIcon.classList.toggle('active');
            }

            const favoritesCheckbox = document.getElementById('favoritesOnlyCheckbox');
            if (favoritesCheckbox && favoritesCheckbox.checked) {
                processFavoritesFilter();
            }
        } else {
            console.error('Ошибка при обновлении избранного:', response.status);
            if (response.status === 401) {
                showAuthModal();
            }
        }
    } catch (error) {
        console.error('Ошибка сети:', error);
    }
}