let currentImageIndex = 0;
let productImages = [];
let currentReviewIndex = 0;
let currentReviewImages = [];

document.addEventListener('DOMContentLoaded', function() {
    initGallery();
    initReviewForm();
    initReviewsSection();
    initReviewGalleries();
});

function initGallery() {
    const thumbnails = document.querySelectorAll('.thumbnail');
    productImages = Array.from(thumbnails).map(thumb => thumb.src);
    
    if (productImages.length > 0) {
        const mainImage = document.getElementById('mainProductImage');
        if (mainImage) {
            mainImage.style.cursor = 'pointer';
            mainImage.addEventListener('click', () => openFullscreen(currentImageIndex));
        }
        
        thumbnails.forEach((thumb, index) => {
            thumb.style.cursor = 'pointer';
            thumb.addEventListener('click', (e) => {
                e.stopPropagation();
                changeMainImage(thumb, index);
                openFullscreen(index);
            });
        });
    }
    
    document.querySelector('.fullscreen-prev')?.addEventListener('click', (e) => {
        e.stopPropagation();
        navigateFullscreen(-1);
    });
    
    document.querySelector('.fullscreen-next')?.addEventListener('click', (e) => {
        e.stopPropagation();
        navigateFullscreen(1);
    });
    
    document.getElementById('fullscreenGallery')?.addEventListener('click', function(e) {
        if (e.target === this || e.target.closest('.close-fullscreen')) {
            closeFullscreen();
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeFullscreen();
            closeFullscreenReviewImage();
        }
    });
}

function changeMainImage(thumbnail, index) {
    const mainImage = document.getElementById('mainProductImage');
    if (mainImage) {
        mainImage.src = thumbnail.src;
        currentImageIndex = index;
        updateActiveThumbnail(index);
    }
}

function updateActiveThumbnail(index) {
    document.querySelectorAll('.thumbnail').forEach(thumb => {
        thumb.classList.remove('active');
    });
    document.querySelectorAll('.thumbnail')[index]?.classList.add('active');
}

function navigate(direction) {
    currentImageIndex = (currentImageIndex + direction + productImages.length) % productImages.length;
    changeMainImage(document.querySelectorAll('.thumbnail')[currentImageIndex], currentImageIndex);
}

function openFullscreen(index) {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
    if (!fullscreenGallery || !fullscreenImage) return;
    
    currentImageIndex = index;
    fullscreenImage.src = productImages[currentImageIndex];
    if (imageCounter) {
        imageCounter.textContent = `${currentImageIndex + 1}/${productImages.length}`;
    }
    fullscreenGallery.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function navigateFullscreen(direction) {
    if (productImages.length === 0) return;
    
    currentImageIndex = (currentImageIndex + direction + productImages.length) % productImages.length;
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
    if (fullscreenImage) {
        fullscreenImage.style.opacity = '0';
        setTimeout(() => {
            fullscreenImage.src = productImages[currentImageIndex];
            if (imageCounter) {
                imageCounter.textContent = `${currentImageIndex + 1}/${productImages.length}`;
            }
            fullscreenImage.style.opacity = '1';
        }, 300);
    }
}

function initReviewsSection() {
    const toggleBtn = document.getElementById('moreReviewsToggle');
    const moreReviews = document.getElementById('moreReviews');
    const reviewItems = document.querySelectorAll('.review-item');
    
    if (!toggleBtn || !moreReviews) return;

    if (reviewItems.length <= 3) {
        toggleBtn.style.display = 'none';
        moreReviews.style.display = 'block';
        return;
    }

    moreReviews.style.display = 'none';
    
    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (moreReviews.style.display === 'none') {
            moreReviews.style.display = 'block';
            this.textContent = 'Скрыть отзывы';
        } else {
            moreReviews.style.display = 'none';
            this.textContent = 'Показать все отзывы';
        }
    });
}

function initReviewForm() {
    const reviewForm = document.getElementById('reviewForm');
    const newReviewForm = document.getElementById('newReviewForm');

    if (newReviewForm) {
        newReviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReview();
        });
    }
}

function showReviewForm() {
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.style.display = reviewForm.style.display === 'none' ? 'block' : 'none';
        if (reviewForm.style.display === 'block') {
            reviewForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

function openReviewFullscreen(element, index, total) {
    const modal = document.getElementById('fullscreenReviewModal');
    const img = document.getElementById('fullscreenReviewImg');
    const counter = document.getElementById('fullscreenReviewCounter');

    if (!modal || !img || !counter) return;

    // Получаем все изображения из галереи этого отзыва
    const gallery = element.closest('.review-thumbnails');
    currentReviewImages = Array.from(gallery.querySelectorAll('.review-thumbnail')).map(el => el.src);

    // Устанавливаем текущий индекс
    currentReviewIndex = index;

    // Загружаем изображение
    img.src = currentReviewImages[currentReviewIndex];
    counter.textContent = `${currentReviewIndex + 1} / ${currentReviewImages.length}`;

    // Показываем модалку
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Добавляем обработчик клавиш
    document.addEventListener('keydown', handleReviewKeydown);
}

function addImageUrlField() {
    const container = document.getElementById('imageUrlsContainer');
    if (!container) return;
    
    const currentFields = container.querySelectorAll('.image-url-input');
    if (currentFields.length >= 5) {
        alert('Максимальное количество изображений - 5');
        return;
    }
    
    const newField = document.createElement('div');
    newField.className = 'image-url-input';
    newField.innerHTML = `
        <input type="text" class="image-url" name="photo_urls" placeholder="Введите URL изображения">
        <button type="button" class="remove-url-btn" onclick="removeImageUrlField(this)">−</button>
    `;
    container.appendChild(newField);
}

function removeImageUrlField(button) {
    const container = document.getElementById('imageUrlsContainer');
    if (!container) return;
    
    const fields = container.querySelectorAll('.image-url-input');
    if (fields.length > 1) {
        button.parentElement.remove();
    } else {
        const input = button.previousElementSibling;
        if (input) input.value = '';
    }
}

async function submitReview() {
    const form = document.getElementById('newReviewForm');
    if (!form) return;

    const formData = new FormData(form);
    const productId = window.location.pathname.split('/').pop();

    try {
        const response = await fetch(`/reviews/create_by/${productId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 1,
                comment: formData.get('comment'),
                grade: parseInt(formData.get('rating')),
                photo_urls: Array.from(formData.getAll('photo_urls')).filter(url => url.trim() !== '')
            })
        });

        if (response.ok) {
            alert('Отзыв успешно добавлен!');
            location.reload();
        } else {
            throw new Error('Ошибка при отправке отзыва');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка: ' + error.message);
    }
}

function toggleSpecs() {
    const specsContent = document.querySelector('.specs-content');
    const toggleBtn = document.querySelector('.specs-toggle');
    
    if (!specsContent || !toggleBtn) return;
    
    const isVisible = specsContent.classList.toggle('show');
    toggleBtn.textContent = isVisible ? '▲' : '▼';
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function closeFullscreenReviewModal() {
    const modal = document.getElementById('fullscreenReviewModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        document.removeEventListener('keydown', handleReviewKeydown);
    }
}

function navigateReviewImage(direction) {
    if (currentReviewImages.length === 0) return;

    currentReviewIndex += direction;

    // Циклическая навигация
    if (currentReviewIndex < 0) {
        currentReviewIndex = currentReviewImages.length - 1;
    } else if (currentReviewIndex >= currentReviewImages.length) {
        currentReviewIndex = 0;
    }

    const img = document.getElementById('fullscreenReviewImg');
    const counter = document.getElementById('fullscreenReviewCounter');

    if (img) {
        img.src = currentReviewImages[currentReviewIndex];
        counter.textContent = `${currentReviewIndex + 1} / ${currentReviewImages.length}`;
    }
}

function handleReviewKeydown(e) {
    if (e.key === 'ArrowLeft') {
        navigateReviewImage(-1);
    } else if (e.key === 'ArrowRight') {
        navigateReviewImage(1);
    } else if (e.key === 'Escape') {
        closeFullscreenReviewModal();
    }
}