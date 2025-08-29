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

function closeFullscreen() {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    if (fullscreenGallery) {
        fullscreenGallery.style.opacity = '0';
        setTimeout(() => {
            fullscreenGallery.style.display = 'none';
            document.body.style.overflow = 'auto';
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

function initReviewGalleries() {
    document.querySelectorAll('.review-gallery').forEach(gallery => {
        const thumbnails = gallery.querySelectorAll('.review-thumbnail');
        if (thumbnails.length > 0) {
            thumbnails[0].classList.add('active');
            
            // Обработчики для миниатюр
            thumbnails.forEach((thumb, index) => {
                thumb.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const mainImg = this.closest('.review-gallery').querySelector('.review-main-image');
                    if (mainImg) {
                        mainImg.src = this.src;
                        thumbnails.forEach(t => t.classList.remove('active'));
                        this.classList.add('active');
                    }
                });
            });
            
            // Обработчик для основного изображения
            const mainImg = gallery.querySelector('.review-main-image');
            if (mainImg) {
                mainImg.addEventListener('click', function() {
                    const activeIndex = Array.from(thumbnails).findIndex(t => t.classList.contains('active'));
                    openFullscreenReviewImage(this.src, activeIndex, thumbnails.length);
                });
            }
        }
    });
}

function openFullscreenReviewImage(src, index, total) {
    const fullscreen = document.getElementById('fullscreenReviewImage');
    const fullscreenImg = document.getElementById('fullscreenReviewImg');
    
    if (!fullscreen || !fullscreenImg) return;
    
    currentReviewIndex = index;
    currentReviewImages = Array.from(document.querySelectorAll('.review-thumbnail')).map(t => t.src);
    
    fullscreenImg.src = src;
    fullscreen.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeFullscreenReviewImage() {
    const fullscreen = document.getElementById('fullscreenReviewImage');
    if (fullscreen) {
        fullscreen.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
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

function selectReviewImage(thumbnail, imageUrl) {
  // Снимаем выделение со всех миниатюр
  document.querySelectorAll('.review-image-thumbnail').forEach(img => {
    img.classList.remove('selected');
  });
  
  // Выделяем текущую миниатюру
  thumbnail.classList.add('selected');
  
  // Обновляем основное изображение
  const mainImage = thumbnail.closest('.review-gallery').querySelector('.review-main-image');
  if (mainImage) {
    mainImage.src = imageUrl;
  }
}

function openReviewFullscreen(imgElement) {
  const gallery = imgElement.closest('.review-gallery');
  const images = Array.from(gallery.querySelectorAll('.review-image-thumbnail')).map(img => img.src);
  const currentIndex = images.indexOf(imgElement.src);
  
  document.getElementById('fullscreenImage').src = imgElement.src;
  currentImageIndex = currentIndex;
  productImages = images; // Используем существующую переменную
  
  openFullscreen(currentIndex);
}

function toggleSpecs() {
    const specsContent = document.querySelector('.specs-content');
    const toggleBtn = document.querySelector('.specs-toggle');
    
    if (!specsContent || !toggleBtn) return;
    
    const isVisible = specsContent.classList.toggle('show');
    toggleBtn.textContent = isVisible ? '▲' : '▼';
}

async function toggleFavorite(button, productId) {
    console.log('toggleFavorite called for product:', productId);
    console.log('Initial button classes:', button.classList.toString());

    try {
        // Проверка аутентификации
        const authCheck = await fetch('/api/check-auth/', {
            credentials: 'include'
        });

        if (!authCheck.ok) {
            showLoginPrompt('Для добавления товаров в избранное необходимо войти в систему');
            return;
        }

        const url = `/favorites/toggle/${productId}`;
        console.log('Fetching:', url);

        // Получаем CSRF токен
        const csrfToken = getCookie('csrftoken') || getCSRFTokenFromMeta();
        console.log('CSRF Token:', csrfToken ? 'Found' : 'Not found');

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'include'
        });

        console.log('Response status:', response.status);

        if (response.ok) {
            const result = await response.json();
            console.log('Server response:', result);

            // Обновляем UI
            button.classList.toggle('active');
            console.log('Button classes after toggle:', button.classList.toString());

            // Анимация
            button.style.transform = 'scale(1.2)';
            setTimeout(() => {
                button.style.transform = 'scale(1)';
            }, 300);

        } else {
            console.error('Server error:', response.status, response.statusText);

            // Детальная информация об ошибке
            try {
                const errorData = await response.json();
                console.error('Error details:', errorData);
            } catch (e) {
                const errorText = await response.text();
                console.error('Error text:', errorText);
            }
        }

    } catch (error) {
        console.error('Network error:', error);
    }
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

function getCSRFTokenFromMeta() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

function getCSRFTokenFromForm() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
}

function getCSRFTokenFromMeta() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

function showLoginPrompt(message) {
    const loginConfirmed = confirm(`${message}. Перейти на страницу входа?`);
    if (loginConfirmed) {
        window.location.href = '/auth/create';
    }
}