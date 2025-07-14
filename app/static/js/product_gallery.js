// Глобальные переменные для галереи
let productImages = [];
let currentImageIndex = 0;

// Инициализация галереи
document.addEventListener('DOMContentLoaded', function() {
    // Получаем все изображения товара из миниатюр
    const thumbnails = document.querySelectorAll('.thumbnail');
    productImages = Array.from(thumbnails).map(thumb => thumb.src);
    
    if (!productImages || productImages.length === 0) {
        productImages = ['data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMjQgMjQiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzY2NiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yMyAxOWEyIDIgMCAwIDEtMiAySDNhMiAyIDAgMCAxLTItMlY1YTIgMiAwIDAgMSAyLTJoNGwyIDJoMTBsMi0yaDRhMiAyIDAgMCAxIDIgMnoiLz48Y2lyY2xlIGN4PSIxMiIgY3k9IjEwIiByPSIzIi8+PHBhdGggZD0iTTE5IDIxYTIgMiAwIDAgMS0yLTJWNyAyIDIgMCAwIDEgMi0yaDJhMiAyIDAgMCAxIDIgMnYxMmEyIDIgMCAwIDEtMiAyeiIvPjwvc3ZnPg=='];
    }
    
    // Обработчик для открытия полноэкранного просмотра
    document.getElementById('mainProductImage').addEventListener('click', function() {
        openFullscreen(currentImageIndex);
    });
    
    // Инициализация раскрытия описания
    initDescriptionToggle();
    
    // Инициализация прокрутки рекомендуемых товаров
    initProductsScroll();
});

// Функция для изменения основного изображения
function changeMainImage(thumbnail, index) {
    currentImageIndex = index;
    const mainImage = document.getElementById('mainProductImage');
    
    // Удаляем active класс у всех миниатюр
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    
    // Добавляем active класс к текущей миниатюре
    thumbnail.classList.add('active');
    
    // Плавная смена изображения
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
    
    // Блокируем прокрутку страницы
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
        
        // Обновляем активную миниатюру
        const thumbnails = document.querySelectorAll('.thumbnail');
        thumbnails.forEach((thumb, idx) => {
            thumb.classList.toggle('active', idx === currentImageIndex);
        });
    }, 200);
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

// Раскрытие описания
function initDescriptionToggle() {
    const desc = document.querySelector('.product-description p');
    if (desc) {
        const fullDesc = desc.textContent;
        if (fullDesc.length > 100) {
            desc.textContent = fullDesc.slice(0, 100) + '...';
            const toggleBtn = document.createElement('button');
            toggleBtn.textContent = 'Показать ещё';
            toggleBtn.style.background = 'none';
            toggleBtn.style.border = 'none';
            toggleBtn.style.color = '#3498db';
            toggleBtn.style.cursor = 'pointer';
            toggleBtn.style.marginLeft = '5px';
            
            toggleBtn.addEventListener('click', () => {
                if (desc.textContent.length > 103) {
                    desc.textContent = fullDesc.slice(0, 100) + '...';
                    toggleBtn.textContent = 'Показать ещё';
                } else {
                    desc.textContent = fullDesc;
                    toggleBtn.textContent = 'Скрыть';
                }
            });
            
            document.querySelector('.product-description').appendChild(toggleBtn);
        }
    }
}

// Прокрутка рекомендуемых товаров
function initProductsScroll() {
    let isDown = false;
    let startX;
    let scrollLeft;
    const slider = document.querySelector('.products-grid');
    
    if (slider) {
        slider.addEventListener('mousedown', (e) => {
            isDown = true;
            startX = e.pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            slider.style.cursor = 'grabbing';
        });
        
        slider.addEventListener('mouseleave', () => {
            isDown = false;
            slider.style.cursor = 'grab';
        });
        
        slider.addEventListener('mouseup', () => {
            isDown = false;
            slider.style.cursor = 'grab';
        });
        
        slider.addEventListener('mousemove', (e) => {
            if(!isDown) return;
            e.preventDefault();
            const x = e.pageX - slider.offsetLeft;
            const walk = (x - startX) * 2;
            slider.scrollLeft = scrollLeft - walk;
        });
    }
}