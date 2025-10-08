let currentImageIndex = 0;
let productImages = [];
let currentReviewIndex = 0;
let currentReviewImages = [];
const defaultImageUrl = "/static/images/default_image.png";

document.addEventListener('DOMContentLoaded', function() {
    initGallery();
    initReviewForm();
    initReviewsSection();
});

function initGallery() {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    if (!fullscreenGallery) {
        console.warn('Элемент #fullscreenGallery не найден');
        return;
    }

    const thumbnails = document.querySelectorAll('.thumbnail');
    productImages = Array.from(thumbnails).map(thumb => thumb.src);

    const mainImage = document.getElementById('mainProductImage');
    if (mainImage) {
        if (productImages.length > 0 && mainImage.src !== productImages[0]) {
            mainImage.src = productImages[0];
            currentImageIndex = 0;
        }

        mainImage.style.cursor = 'pointer';
        mainImage.addEventListener('click', () => openFullscreen(currentImageIndex));
        mainImage.onerror = function() { tryNextProductImage(this); };

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

    fullscreenGallery.addEventListener('click', function(e) {
        if (e.target === this) {
            closeFullscreen();
        }
    });

    document.querySelector('.close-fullscreen')?.addEventListener('click', function(e) {
        e.stopPropagation();
        closeFullscreen();
    });

    document.addEventListener('keydown', function(e) {
        const isFullscreenOpen = window.getComputedStyle(fullscreenGallery).display === 'flex';
        if (!isFullscreenOpen) return;

        if (e.key === 'ArrowLeft') {
            navigateFullscreen(-1);
        } else if (e.key === 'ArrowRight') {
            navigateFullscreen(1);
        } else if (e.key === 'Escape') {
            closeFullscreen();
        }
    });
}

function closeFullscreen() {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    if (fullscreenGallery) {
        fullscreenGallery.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
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

    const gallery = element.closest('.review-thumbnails');
    currentReviewImages = Array.from(gallery.querySelectorAll('.review-thumbnail')).map(el => el.src);

    currentReviewIndex = index;

    img.src = currentReviewImages[currentReviewIndex];
    counter.textContent = `${currentReviewIndex + 1} / ${currentReviewImages.length}`;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

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
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                comment: formData.get('comment'),
                grade: parseInt(formData.get('rating')),
                photo_urls: Array.from(formData.getAll('photo_urls')).filter(url => url.trim() !== '')
            })
        });

        if (response.ok) {
            alert('Отзыв успешно добавлен!');
            location.reload();
        } else {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Неизвестная ошибка сервера');
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

function tryNextProductImage(imgElement) {
    if (currentImageIndex >= productImages.length - 1) {
        imgElement.src = defaultImageUrl;
        console.log("Все изображения продукта недоступны, показываем дефолтное.");
        return;
    }

    currentImageIndex++;
    imgElement.src = productImages[currentImageIndex];
    console.log(`Пробуем изображение #${currentImageIndex + 1}: ${productImages[currentImageIndex]}`);
}