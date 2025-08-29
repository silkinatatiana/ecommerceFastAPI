document.addEventListener('DOMContentLoaded', function() {
    initUserDropdown();
});


function initUserDropdown() {
    const userIcon = document.getElementById('userIcon');
    const userDropdown = document.getElementById('userDropdown');

    if (userIcon && userDropdown) {
        userIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.style.display = userDropdown.style.display === 'block' ? 'none' : 'block';
        });

        document.addEventListener('click', function() {
            userDropdown.style.display = 'none';
        });

        userDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
}