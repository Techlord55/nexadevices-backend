// static/admin/js/image_preview.js

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initImagePreview);
    } else {
        initImagePreview();
    }
    
    function initImagePreview() {
        console.log('Initializing image preview...');
        
        // Get all file inputs for images
        const imageInputs = document.querySelectorAll('input[type="file"][name*="image"]');
        
        imageInputs.forEach(input => {
            // Add change event listener
            input.addEventListener('change', handleImageSelect);
            
            // Add drag and drop support
            const wrapper = input.closest('.form-row');
            if (wrapper) {
                setupDragAndDrop(wrapper, input);
            }
        });
        
        // Watch for dynamically added inlines
        watchForNewInlines();
    }
    
    function handleImageSelect(event) {
        const input = event.target;
        const file = input.files[0];
        
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                showImagePreview(input, e.target.result);
            };
            
            reader.readAsDataURL(file);
        }
    }
    
    function showImagePreview(input, imageSrc) {
        // Find or create preview container
        const formRow = input.closest('.form-row');
        if (!formRow) return;
        
        let previewContainer = formRow.querySelector('.image-preview-container');
        
        if (!previewContainer) {
            previewContainer = document.createElement('div');
            previewContainer.className = 'image-preview-container';
            previewContainer.style.cssText = `
                margin-top: 10px;
                padding: 10px;
                background: #f9f9f9;
                border-radius: 8px;
                text-align: center;
            `;
            
            const inputField = formRow.querySelector('.field-image');
            if (inputField) {
                inputField.appendChild(previewContainer);
            }
        }
        
        previewContainer.innerHTML = `
            <div style="position: relative; display: inline-block;">
                <img src="${imageSrc}" 
                     style="max-width: 200px; 
                            max-height: 200px; 
                            border-radius: 8px; 
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            object-fit: cover;" />
                <div style="margin-top: 8px; font-size: 12px; color: #666;">
                    ✓ Image selected
                </div>
            </div>
        `;
    }
    
    function setupDragAndDrop(wrapper, input) {
        const inputField = wrapper.querySelector('.field-image') || wrapper;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            inputField.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Highlight drop zone when dragging over
        ['dragenter', 'dragover'].forEach(eventName => {
            inputField.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            inputField.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            input.style.borderColor = '#3498db';
            input.style.background = '#e3f2fd';
        }
        
        function unhighlight(e) {
            input.style.borderColor = '#ccc';
            input.style.background = '#f9f9f9';
        }
        
        // Handle dropped files
        inputField.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                input.files = files;
                
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                input.dispatchEvent(event);
            }
        }
    }
    
    function watchForNewInlines() {
        // Watch for clicks on "Add another Product image" button
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList.contains('inline-related')) {
                        const input = node.querySelector('input[type="file"][name*="image"]');
                        if (input) {
                            input.addEventListener('change', handleImageSelect);
                            
                            const wrapper = input.closest('.form-row');
                            if (wrapper) {
                                setupDragAndDrop(wrapper, input);
                            }
                        }
                    }
                });
            });
        });
        
        const inlineGroups = document.querySelectorAll('.inline-group');
        inlineGroups.forEach(group => {
            observer.observe(group, {
                childList: true,
                subtree: true
            });
        });
    }
    
    // Add file size validation
    document.addEventListener('change', function(e) {
        if (e.target.type === 'file' && e.target.name.includes('image')) {
            const file = e.target.files[0];
            if (file) {
                // Check file size (5MB limit)
                const maxSize = 5 * 1024 * 1024; // 5MB in bytes
                
                if (file.size > maxSize) {
                    alert('⚠️ File size too large!\n\nMaximum file size is 5MB.\nCurrent file: ' + 
                          (file.size / 1024 / 1024).toFixed(2) + 'MB\n\n' +
                          'Please compress your image or choose a smaller file.');
                    e.target.value = ''; // Clear the input
                    return;
                }
                
                // Show file info
                console.log('File selected:', {
                    name: file.name,
                    size: (file.size / 1024).toFixed(2) + ' KB',
                    type: file.type
                });
            }
        }
    });
    
})();