/**
 * UI Enhancement for Document Scanner Application
 * Improves user experience with animations and feedback
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main elements
    const mainElements = document.querySelectorAll('h4, .card, .btn, .form-control, .form-select');
    mainElements.forEach((element, index) => {
        element.classList.add('fade-in');
        element.style.animationDelay = `${index * 0.05}s`;
    });

    // Enhance the message display
    const messageElement = document.querySelector('p:not([class])');
    if (messageElement && messageElement.textContent.trim() !== '') {
        // Wrap the message in a styled alert
        const message = messageElement.textContent;
        const alertDiv = document.createElement('div');
        
        if (message.includes('UNABLE')) {
            alertDiv.className = 'alert alert-warning';
            alertDiv.innerHTML = '<strong>Warning:</strong> ' + message;
        } else if (message.includes('Located')) {
            alertDiv.className = 'alert alert-success';
            alertDiv.innerHTML = '<strong>Success:</strong> ' + message;
        } else {
            alertDiv.className = 'alert alert-info';
            alertDiv.innerHTML = '<strong>Info:</strong> ' + message;
        }
        
        messageElement.parentNode.replaceChild(alertDiv, messageElement);
    }

    // Add card wrapper around form elements
    const form = document.querySelector('form');
    if (form) {
        const formParent = form.parentNode;
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card mb-4';
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Move the form inside the card body
        formParent.insertBefore(cardDiv, form);
        cardDiv.appendChild(cardBody);
        cardBody.appendChild(form);
    }

    // Add a title above the canvas without wrapping it in a card to preserve drag functionality
    const canvas = document.getElementById('canvas');
    if (canvas) {
        const canvasParent = canvas.parentNode;
        // Add a title before the canvas
        const cardTitle = document.createElement('h5');
        cardTitle.className = 'text-center mb-3 mt-4';
        cardTitle.textContent = 'Adjust Document Corners';
        
        // Insert the title before the canvas without changing its position
        canvasParent.insertBefore(cardTitle, canvas);
        
        // Style the canvas directly without wrapping
        canvas.style.borderRadius = '8px';
        canvas.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
        canvas.style.backgroundColor = '#fff';
        canvas.style.display = 'block';
        canvas.style.margin = '0 auto';
    }

    // Enhance the model selection dropdown with icons
    const modelSelect = document.getElementById('ocrModel');
    if (modelSelect) {
        // Add a small info text below the dropdown
        const infoText = document.createElement('small');
        infoText.className = 'form-text text-muted mt-1';
        infoText.innerHTML = '<i class="fas fa-info-circle"></i> Pytesseract is faster but Qwen2 may provide better accuracy.';
        modelSelect.parentNode.appendChild(infoText);
    }

    // Enhance the process button
    const processButton = document.getElementById('sendData');
    if (processButton) {
        processButton.classList.add('btn-lg', 'mt-3', 'mb-4');
        
        // Add loading indicator behavior
        processButton.addEventListener('click', function() {
            const btnText = document.getElementById('btn-text');
            const originalText = btnText.textContent;
            
            // Store the original text to restore it if needed
            if (!processButton.getAttribute('data-original-text')) {
                processButton.setAttribute('data-original-text', originalText);
            }
        });
    }
    
    // Add helpful contextual information
    const sendDataBtn = document.getElementById('sendData');
    if (sendDataBtn) {
        const helpText = document.createElement('div');
        helpText.className = 'alert alert-info mt-3 mb-0';
        helpText.innerHTML = '<strong><i class="fas fa-info-circle me-2"></i>Tip:</strong> Drag the yellow corner points to align with the document edges for best results.';
        sendDataBtn.parentNode.appendChild(helpText);
    }
});

// Add interactive canvas guidance
function addCanvasGuidance() {
    const canvas = document.getElementById('canvas');
    if (canvas) {
        // Add a tooltip or popover-like effect when user interacts with the canvas
        canvas.addEventListener('mouseover', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'canvas-tooltip';
            tooltip.textContent = 'Click and drag the yellow circles to adjust document corners';
            tooltip.style.position = 'absolute';
            tooltip.style.top = (canvas.offsetTop - 30) + 'px';
            tooltip.style.left = canvas.offsetLeft + 'px';
            tooltip.style.backgroundColor = 'rgba(0,0,0,0.7)';
            tooltip.style.color = 'white';
            tooltip.style.padding = '5px 10px';
            tooltip.style.borderRadius = '4px';
            tooltip.style.zIndex = '1000';
            tooltip.style.opacity = '0';
            tooltip.style.transition = 'opacity 0.3s ease';
            
            document.body.appendChild(tooltip);
            
            setTimeout(() => {
                tooltip.style.opacity = '1';
            }, 100);
            
            canvas.addEventListener('mouseout', function onMouseOut() {
                tooltip.style.opacity = '0';
                setTimeout(() => {
                    if (document.body.contains(tooltip)) {
                        document.body.removeChild(tooltip);
                    }
                }, 300);
                canvas.removeEventListener('mouseout', onMouseOut);
            });
        });
    }
}

// Call after the page is fully loaded and canvas is initialized
window.addEventListener('load', function() {
    setTimeout(addCanvasGuidance, 1000);
}); 