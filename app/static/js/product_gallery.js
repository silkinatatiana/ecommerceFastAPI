
let currentImageIndex = 0;
let productImages = [];

document.addEventListener('DOMContentLoaded', function() {
    initGallery();
    initReviewForm();
});

// function setupEventListeners() {
//     // Обработчики для свайпов на мобильных устройствах
//     const fullscreenImage = document.getElementById('fullscreenImage');
//     if (fullscreenImage) {
//         let touchStartX = 0;
//         let touchEndX = 0;
        
//         fullscreenImage.addEventListener('touchstart', (e) => {
//             touchStartX = e.changedTouches[0].screenX;
//         }, {passive: true});
        
//         fullscreenImage.addEventListener('touchend', (e) => {
//             touchEndX = e.changedTouches[0].screenX;
//             handleSwipe();
//         }, {passive: true});
//     }
    
//     // Обработчик клика по затемненной области
//     document.getElementById('fullscreenGallery')?.addEventListener('click', (e) => {
//         if (e.target === e.currentTarget) {
//             closeFullscreen();
//         }
//     });
// }

// function handleSwipe() {
//     const SWIPE_THRESHOLD = 50;
//     const diff = touchStartX - touchEndX;
    
//     if (diff > SWIPE_THRESHOLD) {
//         navigateFullscreen(1); // Свайп влево - следующее изображение
//     } else if (diff < -SWIPE_THRESHOLD) {
//         navigateFullscreen(-1); // Свайп вправо - предыдущее изображение
//     }
// }

// function initGallery() {
//     const thumbnails = document.querySelectorAll('.thumbnail');
//     productImages = Array.from(thumbnails).map(thumb => thumb.src);
    
//     if (productImages.length > 0) {
//         const mainImage = document.getElementById('mainProductImage');
//         if (mainImage) {
//             mainImage.style.cursor = 'pointer'; // Просто курсор-указатель
//             mainImage.addEventListener('click', function() {
//                 openFullscreen(currentImageIndex);
//             });
//         }
        
//         // Добавляем обработчики для миниатюр
//         thumbnails.forEach((thumb, index) => {
//             thumb.addEventListener('click', () => {
//                 changeMainImage(thumb, index);
//                 openFullscreen(index);
//             });
//         });

//             // Добавляем обработчики для кнопок навигации в полноэкранном режиме
//         document.querySelector('.fullscreen-prev')?.addEventListener('click', (e) => {
//             e.stopPropagation();
//             navigateFullscreen(-1);
//         });
        
//         document.querySelector('.fullscreen-next')?.addEventListener('click', (e) => {
//             e.stopPropagation();
//             navigateFullscreen(1);
//         });

//          // Обработчик клавиатуры
//         document.addEventListener('keydown', (e) => {
//             if (document.getElementById('fullscreenGallery').style.display === 'flex') {
//                 switch(e.key) {
//                     case 'ArrowLeft': navigateFullscreen(-1); break;
//                     case 'ArrowRight': navigateFullscreen(1); break;
//                     case 'Escape': closeFullscreen(); break;
//                 }
//             }
//         });
//     }
// }

function initGallery() {
    // Собираем все изображения товара
    const thumbnails = document.querySelectorAll('.thumbnail');
    productImages = Array.from(thumbnails).map(thumb => thumb.src);
    
    if (productImages.length > 0) {
        // Главное изображение
        const mainImage = document.getElementById('mainProductImage');
        if (mainImage) {
            mainImage.style.cursor = 'pointer'; // Просто курсор-указатель
            mainImage.addEventListener('click', function() {
                openFullscreen(currentImageIndex);
            });
        }
        
        // Миниатюры
        thumbnails.forEach((thumb, index) => {
            thumb.style.cursor = 'pointer';
            thumb.addEventListener('click', function(e) {
                e.stopPropagation();
                changeMainImage(this, index);
                openFullscreen(index);
            });
        });
    }
    
    // Навигация в полноэкранном режиме
    document.querySelector('.fullscreen-prev')?.addEventListener('click', function(e) {
        e.stopPropagation();
        navigateFullscreen(-1);
    });
    
    document.querySelector('.fullscreen-next')?.addEventListener('click', function(e) {
        e.stopPropagation();
        navigateFullscreen(1);
    });
    
    // Закрытие по клику на фон или крестик
    // document.getElementById('fullscreenGallery')?.addEventListener('click', function(e) {
    //     if (e.target === this || e.target.classList.contains('close-fullscreen')) {
    //         closeFullscreen();
    //     }
    // });

    document.getElementById('fullscreenGallery')?.addEventListener('click', function(e) {
    // Проверяем клик на фон ИЛИ на элемент с классом close-fullscreen ИЛИ его потомков
    if (e.target === this || e.target.closest('.close-fullscreen')) {
        e.preventDefault();  // Предотвращаем стандартное поведение
        e.stopPropagation(); // Останавливаем всплытие события
        closeFullscreen();
    }
});
    
    // Закрытие по ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeFullscreen();
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

function openFullscreen(index) {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
    if (!fullscreenGallery || !fullscreenImage) return;
    
    currentImageIndex = index;
    fullscreenImage.src = productImages[currentImageIndex];
    imageCounter.textContent = `${currentImageIndex + 1}/${productImages.length}`;
    fullscreenGallery.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function navigateFullscreen(direction) {
    currentImageIndex = (currentImageIndex + direction + productImages.length) % productImages.length;
    
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
    fullscreenImage.src = productImages[currentImageIndex];
    imageCounter.textContent = `${currentImageIndex + 1}/${productImages.length}`;
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
        updateActiveThumbnail(index);
        currentImageIndex = index;
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

// Открытие изображения в полноэкранном режиме
function openFullscreen(index) {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
    if (!fullscreenGallery || !fullscreenImage) return;
    
    currentImageIndex = index;
    fullscreenImage.src = productImages[currentImageIndex];
    imageCounter.textContent = `${currentImageIndex + 1} / ${productImages.length}`;
    fullscreenGallery.style.display = 'flex';
    document.body.style.overflow = 'hidden';

        // Плавное появление
    setTimeout(() => {
        fullscreenGallery.style.opacity = '1';
    }, 10);
}

// Навигация в полноэкранном режиме
function navigateFullscreen(direction) {
    if (productImages.length === 0) return;
    
    currentImageIndex = (currentImageIndex + direction + productImages.length) % productImages.length;
    
    const fullscreenImage = document.getElementById('fullscreenImage');
    const imageCounter = document.getElementById('imageCounter');
    
        // Анимация перехода
    fullscreenImage.style.opacity = '0';
    setTimeout(() => {
        fullscreenImage.src = productImages[currentImageIndex];
        imageCounter.textContent = `${currentImageIndex + 1}/${productImages.length}`;
        fullscreenImage.style.opacity = '1';
    }, 300);
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

// Закрытие полноэкранного режима для изображения отзыва
function closeFullscreenReviewImage() {
    const fullscreenReviewImage = document.getElementById('fullscreenReviewImage');
    if (fullscreenReviewImage) {
        fullscreenReviewImage.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initGallery();

    const gallery = document.getElementById('fullscreenGallery');

    if (gallery) {
        // Универсальный обработчик для закрытия
        gallery.addEventListener('click', function(e) {
            // Закрытие по клику на фон
            if (e.target === this) {
                closeFullscreen();
            }
            // Закрытие по клику на крестик (плюс проверка на дочерние элементы)
            else if (e.target.closest('.close-fullscreen')) {
                e.preventDefault();
                e.stopPropagation();
                closeFullscreen();
            }
        });
    }

    // Закрытие по клику вне изображения
    document.getElementById('fullscreenGallery')?.addEventListener('click', function(e) {
        if (e.target === this) {
            closeFullscreen();
        }
    });
    
    // Закрытие по ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeFullscreen();
        }
    });
});

function toggleSpecs() {
    console.log('--- toggleSpecs function called ---');
    
    // Находим элементы
    const specsContent = document.querySelector('.specs-content');
    const toggleBtn = document.querySelector('.specs-toggle');
    
    console.log('Specs content element:', specsContent);
    console.log('Toggle button element:', toggleBtn);
    
    // Проверяем, что элементы существуют
    if (!specsContent || !toggleBtn) {
        console.error('Error: Could not find required elements');
        return;
    }
    
    // Проверяем текущее состояние
    const isCurrentlyVisible = specsContent.classList.contains('show');
    console.log('Current visibility:', isCurrentlyVisible);
    
    // Переключаем класс
    specsContent.classList.toggle('show');
    
    // Обновляем кнопку
    const newState = specsContent.classList.contains('show');
    toggleBtn.textContent = newState ? '▲' : '▼';
    
    console.log('New visibility:', newState);
    console.log('Button text updated to:', toggleBtn.textContent);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    const specsContent = document.querySelector('.specs-content');
    if (specsContent) {
        // Убедимся, что контент изначально скрыт
        specsContent.classList.remove('show');
        console.log('Initialized - specs content hidden');
    }
    
    // Проверяем кнопку
    const toggleBtn = document.querySelector('.specs-toggle');
    if (toggleBtn) {
        toggleBtn.textContent = '▼';
        console.log('Initialized - button set to ▼');
    }
});

// Инициализация формы отзыва
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
        // Переключаем видимость формы
        reviewForm.style.display = reviewForm.style.display === 'none' ? 'block' : 'none';
        
        // Плавная прокрутка к форме
        if (reviewForm.style.display === 'block') {
            reviewForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

// Инициализация - скрываем форму по умолчанию
document.addEventListener('DOMContentLoaded', function() {
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.style.display = 'none';
    }
});

// Добавление поля для URL изображения
function addImageUrlField() {
    const container = document.getElementById('imageUrlsContainer');
    if (!container) return;
    
    // Проверяем количество уже добавленных полей (максимум 5)
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

// Удаление поля для URL изображения
function removeImageUrlField(button) {
    const container = document.getElementById('imageUrlsContainer');
    if (!container) return;
    
    const fields = container.querySelectorAll('.image-url-input');
    if (fields.length > 1) {
        button.parentElement.remove();
    } else {
        // Если это последнее поле, просто очищаем его
        const input = button.previousElementSibling;
        if (input) input.value = '';
    }
}

// Отправка отзыва
async function submitReview() {
    const form = document.getElementById('newReviewForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const productId = window.location.pathname.split('/').pop(); // Получаем ID товара из URL
    
    // Собираем данные формы
    const reviewData = {
        user_id: 1,
        // product_id: parseInt(productId),
        comment: formData.get('comment'),
        grade: parseInt(formData.get('rating')),
        photo_urls: Array.from(formData.getAll('photo_urls')).filter(url => url.trim() !== '')
    };
    
    try {
        const response = await fetch(`/reviews/create_by/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'X-CSRF-Token': getCSRFToken(), // Если используется CSRF защита
            },
            body: JSON.stringify(reviewData)
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Отзыв успешно добавлен!');
            form.reset();
            // Можно обновить список отзывов без перезагрузки страницы
            location.reload(); // Просто перезагружаем страницу для обновления отзывов
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Ошибка при отправке отзыва');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке отзыва: ' + error.message);
    }
}

// Добавление товара в корзину
async function addToCart(productId, quantity = 1) {
    try {
        const response = await fetch('/api/cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'X-CSRF-Token': getCSRFToken(),
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: quantity
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Товар добавлен в корзину!');
            // Можно обновить счетчик корзины в шапке сайта
            updateCartCounter(result.total_items);
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Ошибка при добавлении в корзину');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при добавлении в корзину: ' + error.message);
    }
}

// Обновление счетчика товаров в корзине
function updateCartCounter(count) {
    const cartCounter = document.querySelector('.cart-counter');
    if (cartCounter) {
        cartCounter.textContent = count;
    }
}

// Добавление товара в избранное
async function addToWishlist(productId) {
    try {
        const response = await fetch('/api/wishlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'X-CSRF-Token': getCSRFToken(),
            },
            body: JSON.stringify({
                product_id: productId
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Товар добавлен в избранное!');
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Ошибка при добавлении в избранное');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при добавлении в избранное: ' + error.message);
    }
}

// Обработчики для кнопок "Добавить в корзину" и "В избранное"
document.addEventListener('DOMContentLoaded', function() {
    const addToCartBtn = document.querySelector('.btn-primary');
    const addToWishlistBtn = document.querySelector('.btn-secondary');
    const productId = window.location.pathname.split('/').pop();
    
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function() {
            addToCart(productId);
        });
    }
    
    if (addToWishlistBtn) {
        addToWishlistBtn.addEventListener('click', function() {
            addToWishlist(productId);
        });
    }
});

// Закрытие модальных окон при клике вне их области
window.addEventListener('click', function(event) {
    const fullscreenGallery = document.getElementById('fullscreenGallery');
    if (fullscreenGallery && event.target === fullscreenGallery) {
        closeFullscreen();
    }
    
    const fullscreenReviewImage = document.getElementById('fullscreenReviewImage');
    if (fullscreenReviewImage && event.target === fullscreenReviewImage) {
        closeFullscreenReviewImage();
    }
});

// Закрытие модальных окон при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeFullscreen();
        closeFullscreenReviewImage();
    }
});