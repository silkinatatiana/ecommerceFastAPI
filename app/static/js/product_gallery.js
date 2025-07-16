// Глобальные переменные для галереи
let productImages = [];
let currentImageIndex = 0;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initGallery();
    initSpecsToggle();
});

// Инициализация галереи
function initGallery() {
    const thumbnails = document.querySelectorAll('.thumbnail');
    productImages = Array.from(thumbnails).map(thumb => thumb.src);
    
    if (!productImages || productImages.length === 0) {
        productImages = ['data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMjQgMjQiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzY2NiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yMyAxOWEyIDIgMCAwIDEtMiAySDNhMiAyIDAgMCAxLTItMlY1YTIgMiAwIDAgMSAyLTJoNGwyIDJoMTBsMi0yaDRhMiAyIDAgMCAxIDIgMnoiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEwIiByPSIzIi8+PHBhdGggZD0iTTE5IDIxYTIgMiAwIDAgMS0yLTJWNyAyIDIgMCAwIDEgMi0yaDJhMiAyIDAgMCAxIDIgMnYxMmEyIDIgMCAwIDEtMiAyeiIvPjwvc3ZnPg=='];
    }
    
    document.getElementById('mainProductImage').addEventListener('click', function() {
        openFullscreen(currentImageIndex);
    });
}

// Инициализация переключения характеристик
function initSpecsToggle() {
    const specsContent = document.querySelector('.specs-content');
    const toggleBtn = document.querySelector('.specs-toggle');
    
    if (specsContent && toggleBtn) {
        // По умолчанию скрываем характеристики
        specsContent.classList.remove('show');
        toggleBtn.textContent = '▼';
    }
}

// Функция для изменения основного изображения
function changeMainImage(thumbnail, index) {
    currentImageIndex = index;
    const mainImage = document.getElementById('mainProductImage');
    
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    
    thumbnail.classList.add('active');
    
    mainImage.style.opacity = 0;
    setTimeout(() => {
        mainImage.src = productImages[index];
        mainImage.style.opacity = 1;
    }, 150);
}

// Навигация по изображениям
function navigate(direction) {
    if (productImages.length <= 1) return;
    
    currentImageIndex = (currentImageIndex + direction + productImages.length) % productImages.length;
    const thumbnails = document.querySelectorAll('.thumbnail');
    if (thumbnails[currentImageIndex]) {
        changeMainImage(thumbnails[currentImageIndex], currentImageIndex);
    }
}

// Открытие полноэкранного просмотра
function openFullscreen(index) {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
    currentImageIndex = index;
    fullscreenImage.src = productImages[index];
    imageCounter.textContent = `${index + 1} / ${productImages.length}`;
    fullscreenGallery.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Закрытие полноэкранного просмотра
function closeFullscreen() {
    document.getElementById('fullscreenGallery').style.display = 'none';
    document.body.style.overflow = '';
}

// Навигация в полноэкранном режиме
function navigateFullscreen(direction) {
    if (productImages.length <= 1) return;
    
    currentImageIndex = (currentImageIndex + direction + productImages.length) % productImages.length;
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
    fullscreenImage.style.opacity = 0;
    setTimeout(() => {
        fullscreenImage.src = productImages[currentImageIndex];
        imageCounter.textContent = `${currentImageIndex + 1} / ${productImages.length}`;
        fullscreenImage.style.opacity = 1;
        
        const thumbnails = document.querySelectorAll('.thumbnail');
        thumbnails.forEach((thumb, idx) => {
            thumb.classList.toggle('active', idx === currentImageIndex);
        });
    }, 200);
}

// Переключение характеристик
function toggleSpecs() {
    const specsContent = document.querySelector('.specs-content');
    const toggleBtn = document.querySelector('.specs-toggle');
    
    if (specsContent && toggleBtn) {
        specsContent.classList.toggle('show');
        toggleBtn.textContent = specsContent.classList.contains('show') ? '▲' : '▼';
    }
}

// Обработчики клавиатуры для полноэкранного просмотра
document.addEventListener('keydown', function(e) {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    if (fullscreenGallery.style.display === 'flex') {
        if (e.key === 'Escape') {
            closeFullscreen();
        } else if (e.key === 'ArrowLeft') {
            navigateFullscreen(-1);
        } else if (e.key === 'ArrowRight') {
            navigateFullscreen(1);
        }
    }
});