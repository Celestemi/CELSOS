document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const showRegister = document.getElementById('showRegister');
    const showLogin = document.getElementById('showLogin');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const themeSelect = document.getElementById('themeSelect');
    
    // Verificar si los elementos existen antes de añadir event listeners
    if (showRegister && showLogin && loginForm && registerForm) {
        // Mostrar formulario de registro
        showRegister.addEventListener('click', function(e) {
            e.preventDefault();
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
            showRegister.style.display = 'none';
            showLogin.style.display = 'block';
        });
        
        // Mostrar formulario de login
        showLogin.addEventListener('click', function(e) {
            e.preventDefault();
            registerForm.style.display = 'none';
            loginForm.style.display = 'block';
            showRegister.style.display = 'block';
            showLogin.style.display = 'none';
        });
    }
    
    // Selector de tema (si existe en la página)
    if (themeSelect) {
        themeSelect.addEventListener('change', function() {
            const selectedTheme = this.value;
            document.body.className = selectedTheme;
            
            // Guardar en localStorage
            localStorage.setItem('theme', selectedTheme);
        });
        
        // Cargar tema guardado al iniciar
        const savedTheme = localStorage.getItem('theme') || 'theme-dark';
        document.body.className = savedTheme;
        themeSelect.value = savedTheme;
    }
    
    // Validación de formularios
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Validación básica de campos requeridos
            const inputs = this.querySelectorAll('input[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.style.borderColor = 'red';
                    isValid = false;
                } else {
                    input.style.borderColor = '';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Por favor completa todos los campos requeridos');
            }
        });
    });
});