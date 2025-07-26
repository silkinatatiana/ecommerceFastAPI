function switchTab(tabName) {
            // Переключение активной вкладки
            document.querySelectorAll('.auth-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelector(`.auth-tab[onclick="switchTab('${tabName}')"]`).classList.add('active');

            // Переключение активной формы
            document.querySelectorAll('.auth-form').forEach(form => {
                form.classList.remove('active');
            });
            document.getElementById(`${tabName}-form`).classList.add('active');
        }