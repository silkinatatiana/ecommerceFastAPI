// static/js/product_gallery.js
document.addEventListener('DOMContentLoaded', function() {
    // Переключение между изображениями в галерее
    const thumbnails = document.querySelectorAll('.thumbnail');
    const mainImage = document.querySelector('.product-main-image');
    
    // Проверяем, есть ли миниатюры на странице
    if (thumbnails.length > 0 && mainImage) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                // Удаляем active класс у всех миниатюр
                thumbnails.forEach(t => t.classList.remove('active'));
                
                // Добавляем active класс к текущей миниатюре
                this.classList.add('active');
                
                // Обновляем главное изображение
                mainImage.src = this.src;
                
                // Добавляем анимацию перехода
                mainImage.style.opacity = 0;
                setTimeout(() => {
                    mainImage.style.opacity = 1;
                }, 100);
            });
        });
    }
});