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
            
            // Create header with title and clear button
            const headerDiv = document.createElement('div');
            headerDiv.className = 'category-header';
            
            const categoryHeader = document.createElement('h3');
            categoryHeader.className = 'category-title';
            categoryHeader.textContent = categoryName;
            headerDiv.appendChild(categoryHeader);
            
            // Create clear button
            const clearBtn = document.createElement('button');
            clearBtn.className = 'btn-clear-category';
            clearBtn.textContent = '✕ Clear';
            clearBtn.onclick = (e) => {
                e.stopPropagation();
                clearCategory(categoryName);
            };
            headerDiv.appendChild(clearBtn);
            
            categoryDiv.appendChild(headerDiv);
            
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
        
        // Select default buttons after categories are created
        const defaultButtons = ['PBE', 'NCORE', 'LAPACK', 'WRITE'];
        defaultButtons.forEach(buttonName => {
            const btn = document.querySelector(`#btn-${buttonName.replace(/[\s-]/g, '_').toLowerCase()}`);
            if (btn) {
                const category = btn.dataset.category;
                // For Functional category, we need to handle it as single-select
                if (category === 'Functional') {
                    const functionalBtns = document.querySelectorAll('.task-btn[data-category="Functional"]');
                    functionalBtns.forEach(b => b.classList.remove('active'));
                }
                btn.classList.add('active');
                selectedTasks.push(buttonName);
            }
        });
        
        // Load default task parameters
        loadTaskParameters(selectedTasks);
    })
    .catch(error => console.error('Error loading task categories:', error));
}

/**
 * Clear all selections in a category
 */
function clearCategory(categoryName) {
    // Get all buttons in this category
    const buttons = document.querySelectorAll(`.task-btn[data-category="${categoryName}"]`);
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Remove from selectedTasks array
    selectedTasks = selectedTasks.filter(task => {
        const btn = document.querySelector(`#btn-${task.replace(/[\s-]/g, '_').toLowerCase()}`);
        return btn && btn.dataset.category !== categoryName;
    });
    
    // Clear task parameters display
    document.getElementById('taskParams').innerHTML = '<p class="info-text">Select tasks to see their parameters</p>';
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
 * Handle task selection (single-select for Functional and vdW, multi-select for others)
 */
function selectTask(taskName, buttonElement, categoryName) {
    // vdW buttons are mutually exclusive (single-select within the group)
    const vdWButtons = ['D3-0', 'D3-BJ', 'D4'];
    const isVdWButton = vdWButtons.includes(taskName);
    
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
    } else if (isVdWButton) {
        // vdW single-select: deselect other vdW buttons but keep non-vdW corrections
        const allVdWButtons = Array.from(document.querySelectorAll('.task-btn')).filter(btn => 
            vdWButtons.includes(btn.textContent)
        );
        allVdWButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Select only the clicked button
        buttonElement.classList.add('active');
        
        // Update selectedTasks: remove all vdW tasks, add the new one
        selectedTasks = selectedTasks.filter(task => !vdWButtons.includes(task));
        selectedTasks.push(taskName);
    } else {
        // Multi-select for other buttons (Correction except vdW, Model, System, Tasks)
        if (buttonElement.classList.contains('active')) {
            buttonElement.classList.remove('active');
            selectedTasks = selectedTasks.filter(task => task !== taskName);
        } else {
            buttonElement.classList.add('active');
            selectedTasks.push(taskName);
            
            // Special handling: if Frequency is selected, auto-unselect NCORE
            if (taskName === 'Frequency') {
                const ncoreBtn = document.querySelector('#btn-ncore');
                if (ncoreBtn && ncoreBtn.classList.contains('active')) {
                    ncoreBtn.classList.remove('active');
                    selectedTasks = selectedTasks.filter(task => task !== 'NCORE');
                }
            }
            
            // Special handling: if NCORE is selected and Frequency is active, unselect Frequency
            if (taskName === 'NCORE') {
                const frequencyBtn = document.querySelector('#btn-frequency');
                if (frequencyBtn && frequencyBtn.classList.contains('active')) {
                    frequencyBtn.classList.remove('active');
                    selectedTasks = selectedTasks.filter(task => task !== 'Frequency');
                }
            }
            
            // Mutually exclusive group: Dimer, Opt, Frequency, Single, TSopt, MD, NEB
            // Only one of these can be selected at a time
            const mutuallyExclusiveTasks = ['Dimer', 'Opt', 'Frequency', 'Single', 'TSopt', 'MD', 'NEB'];
            if (mutuallyExclusiveTasks.includes(taskName)) {
                // Unselect all other tasks in this group
                mutuallyExclusiveTasks.forEach(task => {
                    if (task !== taskName) {
                        const btn = document.querySelector(`#btn-${task.replace(/[\s-]/g, '_').toLowerCase()}`);
                        if (btn && btn.classList.contains('active')) {
                            btn.classList.remove('active');
                            selectedTasks = selectedTasks.filter(t => t !== task);
                        }
                    }
                });
            }
            
            // Auto-calculate DFT+U parameters if DFT+U is selected
            if (taskName === 'DFT+U') {
                calculateDFTUParams();
            }
            
            // Auto-calculate MAGMOM if ISPIN is selected
            if (taskName === 'ISPIN') {
                calculateMagmom();
            }
            
            // Auto-calculate IMAGES if NEB is selected
            if (taskName === 'NEB') {
                calculateNEBImages();
            }
        }
    }
    
    // Load task parameters for all selected tasks
    loadTaskParameters(selectedTasks);
}

/**
 * Auto-calculate DFT+U parameters from POSCAR
 */
function calculateDFTUParams() {
    fetch('/api/calculate-dftu', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✓ DFT+U parameters calculated:', data);
            // Store calculated values for later use in INCAR generation
            window.dftuParams = {
                'LDAUL': data.LDAUL,
                'LDAUU': data.LDAUU,
                'LDAUJ': data.LDAUJ
            };
        } else {
            console.log('Could not auto-calculate DFT+U:', data.error);
        }
    })
    .catch(error => console.log('DFT+U calculation not available:', error));
}

/**
 * Auto-calculate MAGMOM from POSCAR
 */
function calculateMagmom() {
    fetch('/api/calculate-magmom', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✓ MAGMOM calculated:', data.MAGMOM);
            // Store calculated MAGMOM for later use
            window.magmomValue = data.MAGMOM;
        } else {
            console.log('Could not auto-calculate MAGMOM:', data.error);
        }
    })
    .catch(error => console.log('MAGMOM calculation not available:', error));
}

/**
 * Auto-calculate NEB IMAGES from folder count
 */
function calculateNEBImages() {
    fetch('/api/calculate-neb-images', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✓ NEB IMAGES calculated:', data.IMAGES);
            // Store calculated IMAGES value
            window.nebImages = data.IMAGES;
        } else {
            console.log('Could not auto-calculate NEB IMAGES:', data.error);
        }
    })
    .catch(error => console.log('NEB calculation not available:', error));
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
 * Display task parameters in a readable format with task sections
 */
function displayTaskParams(params) {
    const taskParamsDiv = document.getElementById('taskParams');
    
    if (!selectedTasks || selectedTasks.length === 0) {
        taskParamsDiv.innerHTML = '<p class="info-text">Select a task to see its parameters</p>';
        return;
    }
    
    taskParamsDiv.innerHTML = '';
    taskParamsDiv.className = 'parameter-sections';
    
    // List of non-task items to filter out
    const nonTaskItems = ['PBE', 'RPBE', 'R2SCAN', 'HSE06', 'D3-0', 'D3-BJ', 'D4', 'Vaspsol', 'DFT+U', 'Gas', 'Bulk', 'Slab', 'Mixer', 'Dipole', 'LAPACK', 'NCORE', 'WRITE'];
    
    // Get only actual task items
    const taskItems = selectedTasks.filter(task => !nonTaskItems.includes(task));
    
    if (taskItems.length === 0) {
        taskParamsDiv.innerHTML = '<p class="info-text">Select a task to see its parameters</p>';
        return;
    }
    
    // Display each task
    taskItems.forEach(taskName => {
        fetch('/api/task-params', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ task: taskName })
        })
        .then(response => response.json())
        .then(data => {
            if (Object.keys(data.params).length > 0) {
                const taskSection = document.createElement('div');
                taskSection.className = 'param-section';
                
                const sectionLabel = document.createElement('label');
                sectionLabel.style.fontWeight = '700';
                sectionLabel.style.color = '#0099cc';
                sectionLabel.style.cursor = 'default';
                sectionLabel.style.fontSize = '0.9em';
                sectionLabel.textContent = taskName;
                taskSection.appendChild(sectionLabel);
                
                const sectionContent = document.createElement('div');
                sectionContent.className = 'section-content';
                
                Object.entries(data.params).forEach(([key, value]) => {
                    const p = document.createElement('p');
                    p.innerHTML = `<strong>${key}</strong> = ${value}`;
                    sectionContent.appendChild(p);
                });
                
                taskSection.appendChild(sectionContent);
                taskParamsDiv.appendChild(taskSection);
            }
        })
        .catch(error => console.error('Error loading task params for ' + taskName + ':', error));
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
        // Skip the system section (SYSTEM parameter is handled separately and always included)
        if (sectionKey === 'd_system') {
            return;
        }
        
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
    console.log('generateINCAR called');
    console.log('selectedTasks:', selectedTasks);
    
    try {
        // Get included standard sections
        const includeSections = {};
        const paramSections = document.querySelectorAll('.param-section');
        console.log('Found param sections:', paramSections.length);
        
        paramSections.forEach(section => {
            const sectionKey = section.dataset.section;
            const checkbox = section.querySelector('input[type="checkbox"]');
            if (checkbox && sectionKey) {
                includeSections[sectionKey] = checkbox.checked;
            }
        });
        
        // Get custom parameters
        const customParams = {};
        const paramRows = document.querySelectorAll('.param-input-row');
        console.log('Found custom param rows:', paramRows.length);
        
        paramRows.forEach(row => {
            const keyInput = row.querySelector('.param-key');
            const valueInput = row.querySelector('.param-value');
            if (keyInput && valueInput) {
                const key = keyInput.value;
                const value = valueInput.value;
                if (key && value) {
                    customParams[key] = value;
                }
            }
        });
        
        // Add auto-calculated DFT+U parameters if available
        if (window.dftuParams && selectedTasks.includes('DFT+U')) {
            Object.assign(customParams, window.dftuParams);
        }
        
        // Add auto-calculated MAGMOM if available
        if (window.magmomValue && selectedTasks.includes('ISPIN')) {
            customParams['MAGMOM'] = window.magmomValue;
        }
        
        // Add auto-calculated NEB IMAGES if available
        if (window.nebImages && selectedTasks.includes('NEB')) {
            customParams['IMAGES'] = window.nebImages;
        }
        
        const requestBody = {
            tasks: selectedTasks,
            include_sections: includeSections,
            custom_params: customParams
        };
        
        console.log('Request body:', requestBody);
        
        // Send to backend
        fetch('/api/generate-incar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            displayINCAR(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error generating INCAR: ' + error.message);
        });
    } catch (error) {
        console.error('Exception in generateINCAR:', error);
        alert('Exception: ' + error.message);
    }
}

/**
 * Display generated INCAR
 */
function displayINCAR(data) {
    console.log('displayINCAR called with data:', data);
    
    const preview = document.getElementById('incarPreview');
    const stats = document.getElementById('previewStats');
    const downloadBtn = document.getElementById('downloadBtn');
    
    if (data.error) {
        console.error('API error:', data.error);
        preview.value = 'Error: ' + data.error;
        stats.innerHTML = '<strong style="color: red;">Error generating INCAR</strong>';
        downloadBtn.disabled = true;
        return;
    }
    
    if (!data.incar_content) {
        console.error('No incar_content in response');
        preview.value = 'Error: No INCAR content generated';
        stats.innerHTML = '<strong style="color: red;">Error: Empty response</strong>';
        downloadBtn.disabled = true;
        return;
    }
    
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
