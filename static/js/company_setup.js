document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('company-setup-form');
    const logoUrlInput = document.getElementById('logo_url');
    const logoPreview = document.getElementById('logo-preview');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        if (validateForm()) {
            this.submit();
        }
    });
    
    logoUrlInput.addEventListener('input', function() {
        updateLogoPreview(this.value);
    });
});

function validateForm() {
    let isValid = true;
    const requiredFields = document.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

function updateLogoPreview(url) {
    const logoPreview = document.getElementById('logo-preview');
    
    if (url) {
        logoPreview.src = url;
        logoPreview.style.display = 'block';
    } else {
        logoPreview.src = '';
        logoPreview.style.display = 'none';
    }
}
