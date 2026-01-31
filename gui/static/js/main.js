// Q-robot INCAR Generator - JavaScript

let selectedTasks = [];  // Changed from selectedTask to selectedTasks array
let currentParams = {};
// Tasks variable is now defined in index.html template
// INCAR content is now stored in textarea#incarPreview instead of a variable

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeTaskCategories();
    loadStandardParameters();
});

/**
 * Initialize task categories with buttons
 */
function initializeTaskCategories() {
    const categoriesContainer = document.getElementById('taskCategories');
    categoriesContainer.innerHTML = '';
    
    // Fetch task categories from backend
    fetch('/api/task-categories')
    .then(response => response.json())
    .then(data => {
        const categories = data.categories;
        
        // Create category sections - categories is now an array to preserve order
        categories.forEach((categoryObj) => {
            const categoryName = categoryObj.name;
            const tasks = categoryObj.tasks;
            
            // Create category header
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'task-category';
            
            const categoryHeader = document.createElement('h3');
            categoryHeader.className = 'category-title';
            categoryHeader.textContent = categoryName;
            categoryDiv.appendChild(categoryHeader);
            
            // Create button container for this category
            const buttonsDiv = document.createElement('div');
            buttonsDiv.className = 'task-buttons';
            
            // Create buttons for each task in category
            Object.entries(tasks).forEach(([taskKey, taskData]) => {
                const btn = document.createElement('button');
                btn.className = 'task-btn';
                btn.textContent = taskKey;
                btn.id = 'btn-' + taskKey.replace(/[\s-]/g, '_').toLowerCase();
                btn.dataset.category = categoryName;  // Store category for single vs multi-select logic
                btn.onclick = () => selectTask(taskKey, btn, categoryName);
                buttonsDiv.appendChild(btn);
            });
            
            categoryDiv.appendChild(buttonsDiv);
            categoriesContainer.appendChild(categoryDiv);
        });
    })
    .catch(error => console.error('Error loading task categories:', error));
}

/**
 * Initialize task buttons (deprecated - keeping for backward compatibility)
 */
function initializeTasks() {
    initializeTaskCategories();
}

/**
 * Select task by name
 */
function selectTaskByName(taskName) {
    const buttons = document.querySelectorAll('.task-btn');
    for (let btn of buttons) {
        if (btn.textContent === taskName) {
            selectTask(taskName, btn);
            break;
        }
    }
}

/**
 * Handle task selection (single-select for Functional, multi-select for others)
 */
function selectTask(taskName, buttonElement, categoryName) {
    // Check if this is the Functional category (single-select)
    if (categoryName === 'Functional') {
        // Single-select: deselect all other buttons in this category
        const allButtons = document.querySelectorAll('.task-btn[data-category="Functional"]');
        allButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Select only the clicked button
        buttonElement.classList.add('active');
        
        // Update selectedTasks: remove all Functional tasks, add the new one
        selectedTasks = selectedTasks.filter(task => {
            // Keep tasks that are not from Functional category
            const btn = document.querySelector(`#btn-${task.replace(/[\s-]/g, '_').toLowerCase()}`);
            return btn && btn.dataset.category !== 'Functional';
        });
        selectedTasks.push(taskName);
    } else {
        // Multi-select for Correction, System, Tasks
        if (buttonElement.classList.contains('active')) {
            buttonElement.classList.remove('active');
            selectedTasks = selectedTasks.filter(task => task !== taskName);
        } else {
            buttonElement.classList.add('active');
            selectedTasks.push(taskName);
        }
    }
    
    // Load task parameters for all selected tasks
    loadTaskParameters(selectedTasks);
}

/**
 * Load parameters for selected tasks
 */
function loadTaskParameters(taskNames) {
    const taskParamsDiv = document.getElementById('taskParams');
    
    if (!taskNames || taskNames.length === 0) {
        taskParamsDiv.innerHTML = '<p class="info-text">Select tasks to see their parameters</p>';
        currentParams = {};
        return;
    }
    
    taskParamsDiv.innerHTML = '<p class="info-text">Loading...</p>';
    
    // Fetch parameters for all selected tasks
    let allParams = {};
    let loadedCount = 0;
    
    taskNames.forEach(taskName => {
        fetch('/api/task-params', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ task: taskName })
        })
        .then(response => response.json())
        .then(data => {
            allParams = { ...allParams, ...data.params };
            loadedCount++;
            if (loadedCount === taskNames.length) {
                displayTaskParams(allParams);
                currentParams = allParams;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadedCount++;
            if (loadedCount === taskNames.length) {
                displayTaskParams(allParams);
                currentParams = allParams;
            }
        });
    });
}

/**
 * Display task parameters in a readable format
 */
function displayTaskParams(params) {
    const taskParamsDiv = document.getElementById('taskParams');
    taskParamsDiv.innerHTML = '';
    
    if (Object.keys(params).length === 0) {
        taskParamsDiv.innerHTML = '<p class="info-text">No parameters for this task</p>';
        return;
    }
    
    Object.entries(params).forEach(([key, value]) => {
        const paramItem = document.createElement('div');
        paramItem.className = 'param-item';
        paramItem.innerHTML = `<strong>${key}</strong> = ${value}`;
        taskParamsDiv.appendChild(paramItem);
    });
}

/**
 * Load and display standard parameters
 */
function loadStandardParameters() {
    fetch('/api/standard-params')
    .then(response => response.json())
    .then(data => {
        displayStandardParameters(data.standard);
    })
    .catch(error => console.error('Error:', error));
}

/**
 * Display standard parameter sections as checkboxes
 */
function displayStandardParameters(standardParams) {
    const sectionsDiv = document.getElementById('standardSections');
    sectionsDiv.innerHTML = '';
    
    Object.entries(standardParams).forEach(([sectionKey, sectionParams]) => {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'param-section';
        sectionDiv.dataset.section = sectionKey;
        
        // Create checkbox (checked by default)
        const label = document.createElement('label');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = true;  // Set as default checked
        checkbox.onchange = () => toggleSection(sectionDiv);
        
        // Section title
        const sectionName = sectionKey.replace('d_', '').replace(/_/g, ' ').toUpperCase();
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(sectionName));
        
        sectionDiv.appendChild(label);
        sectionDiv.classList.add('checked');  // Add checked class for styling
        
        // Section content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'section-content';
        Object.entries(sectionParams).forEach(([key, value]) => {
            const p = document.createElement('p');
            p.innerHTML = `<strong>${key}</strong> = ${value}`;
            contentDiv.appendChild(p);
        });
        sectionDiv.appendChild(contentDiv);
        
        sectionsDiv.appendChild(sectionDiv);
    });
}

/**
 * Toggle section checkbox
 */
function toggleSection(sectionDiv) {
    const checkbox = sectionDiv.querySelector('input[type="checkbox"]');
    if (checkbox.checked) {
        sectionDiv.classList.add('checked');
    } else {
        sectionDiv.classList.remove('checked');
    }
}

/**
 * Add custom parameter input
 */
function addCustomParam() {
    const container = document.getElementById('customParamsContainer');
    const newRow = document.createElement('div');
    newRow.className = 'param-input-row';
    newRow.innerHTML = `
        <input type="text" class="param-key" placeholder="Parameter name (e.g., ISPIN)">
        <input type="text" class="param-value" placeholder="Value (e.g., 2)">
        <button class="btn-remove" onclick="removeCustomParam(this)">✕</button>
    `;
    container.appendChild(newRow);
}

/**
 * Remove custom parameter input
 */
function removeCustomParam(button) {
    button.closest('.param-input-row').remove();
}

/**
 * Generate INCAR file
 */
function generateINCAR() {
    // Get included standard sections
    const includeSections = {};
    document.querySelectorAll('.param-section').forEach(section => {
        const sectionKey = section.dataset.section;
        const isChecked = section.querySelector('input[type="checkbox"]').checked;
        includeSections[sectionKey] = isChecked;
    });
    
    // Get custom parameters
    const customParams = {};
    document.querySelectorAll('.param-input-row').forEach(row => {
        const key = row.querySelector('.param-key').value;
        const value = row.querySelector('.param-value').value;
        if (key && value) {
            customParams[key] = value;
        }
    });
    
    // Send to backend
    fetch('/api/generate-incar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tasks: selectedTasks,  // Changed from task to tasks (array)
            include_sections: includeSections,
            custom_params: customParams
        })
    })
    .then(response => response.json())
    .then(data => {
        displayINCAR(data);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error generating INCAR');
    });
}

/**
 * Display generated INCAR
 */
function displayINCAR(data) {
    const preview = document.getElementById('incarPreview');
    const stats = document.getElementById('previewStats');
    const downloadBtn = document.getElementById('downloadBtn');
    
    preview.value = data.incar_content;
    
    stats.innerHTML = `
        <strong>Parameters:</strong> ${data.param_count} | 
        <strong>Lines:</strong> ${data.incar_content.split('\n').length}
    `;
    
    downloadBtn.disabled = false;
}


/**
 * Download INCAR file
 */
function downloadINCAR() {
    let preview = document.getElementById("incarPreview");
    if (!preview.value) {
        alert('Please generate INCAR first');
        return;
    }
    
    fetch('/api/download-incar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: preview.value
        })
    })
    .then(response => response.blob())
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'INCAR';
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error downloading file');
    });
}

/**
 * Copy INCAR to clipboard
 */
function copyToClipboard() {
    let preview = document.getElementById("incarPreview");
    if (!preview.value) {
        alert("Please generate INCAR first!");
        return;
    }
    navigator.clipboard.writeText(preview.value).then(() => {
        alert('INCAR copied to clipboard!');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error copying to clipboard');
    });
}

/**
 * Reset the entire form
 */
function resetForm() {
    if (!confirm('Are you sure you want to reset all settings?')) {
        return;
    }
    
    // Clear selected tasks
    selectedTasks = [];
    document.querySelectorAll('.task-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Uncheck all sections
    document.querySelectorAll('.param-section input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
        checkbox.closest('.param-section').classList.remove('checked');
    });
    
    // Clear custom parameters (keep only one empty row)
    const container = document.getElementById('customParamsContainer');
    const rows = container.querySelectorAll('.param-input-row');
    rows.forEach((row, index) => {
        if (index === 0) {
            row.querySelector('.param-key').value = '';
            row.querySelector('.param-value').value = '';
        } else {
            row.remove();
        }
    });
    
    // Clear preview
    document.getElementById('incarPreview').value = '';
    document.getElementById('previewStats').innerHTML = '';
    document.getElementById('taskParams').innerHTML = '<p class="info-text">Select tasks to see their parameters</p>';
    document.getElementById('downloadBtn').disabled = true;
    
    currentParams = {};
}
