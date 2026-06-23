// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show success feedback
        const btn = document.getElementById('copyBtn');
        if (btn) {
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '✅ Copied!';
            btn.classList.add('bg-emerald-700');
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.classList.remove('bg-emerald-700');
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard. Please select and copy manually.');
    });
}

// Copy letter function (used in dispute_letter.html)
function copyLetter() {
    const text = document.getElementById('appealText').innerText;
    copyToClipboard(text);
}

// Auto-hide loading overlay after timeout (safety net)
document.addEventListener('DOMContentLoaded', function() {
    // If loading overlay stays visible for more than 60 seconds, hide it
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        setTimeout(() => {
            if (loadingOverlay.style.opacity !== '0') {
                loadingOverlay.style.opacity = '0';
                loadingOverlay.style.pointerEvents = 'none';
            }
        }, 60000);
    }
});

// File input auto-submit
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                this.form.requestSubmit();
            }
        });
    }
});

// Console log for debugging
console.log('Medical Billing Auditor loaded successfully!');