#!/usr/bin/env python3
"""
INCAR Generator Web Interface
A Flask-based GUI for generating VASP INCAR files using the brain.incar module.
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO
import json

# Add brain folder to path to import incar module
# Use absolute path to ensure it works from any location
brain_path = Path(__file__).resolve().parent.parent / 'brain'
sys.path.insert(0, str(brain_path))

# Verify the path exists
if not brain_path.exists():
    print(f"Error: Brain module not found at {brain_path}")
    sys.exit(1)

from incar import standard_incar, tasks_incar

# Try to import data module for DFT+U and ISPIN calculations
try:
    from data import u_value, j_value, mag_value
    HAS_DATA_MODULE = True
except ImportError:
    HAS_DATA_MODULE = False
    u_value = {}
    j_value = {}
    mag_value = {}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Load task categories from configuration file
config_path = Path(__file__).resolve().parent / 'task_config.json'
if config_path.exists():
    with open(config_path, 'r') as f:
        TASK_CATEGORIES = json.load(f)
else:
    print(f"Warning: task_config.json not found at {config_path}")
    TASK_CATEGORIES = {}

# Get available tasks from incar module
# Create mapping from task key to readable name
TASK_MAPPING = {}
for key in tasks_incar.keys():
    # Convert d_cal_something to Something
    readable_name = key.replace('d_cal_', '')
    # Handle special cases like vdwD3bj -> vdW-D3-BJ
    if 'vdw' in readable_name.lower():
        if 'bj' in readable_name:
            readable_name = 'vdW-D3-BJ'
        elif 'zero' in readable_name:
            readable_name = 'vdW-D3-Zero'
    elif 'ml' in readable_name.lower():
        # ML cases: mltrain -> ML-Train
        parts = readable_name.split('ml')
        readable_name = 'ML-' + parts[1].capitalize()
    else:
        # Standard case: convert underscores to spaces and title case
        readable_name = readable_name.replace('_', ' ').title()
    
    TASK_MAPPING[key] = {
        'display': readable_name,
        'params': tasks_incar[key]
    }

AVAILABLE_TASKS = [TASK_MAPPING[key]['display'] for key in sorted(TASK_MAPPING.keys())]
TASK_KEYS = {value['display'].lower().replace(' ', '_').replace('-', ''): key for key, value in TASK_MAPPING.items()}

# Merge categorized tasks from config file into TASK_MAPPING
for category, tasks in TASK_CATEGORIES.items():
    for task_name, task_data in tasks.items():
        TASK_MAPPING[task_name] = {
            'display': task_name,
            'params': task_data['params'],
            'category': category
        }

AVAILABLE_TASKS = [TASK_MAPPING[key]['display'] for key in sorted(TASK_MAPPING.keys())]
TASK_KEYS = {value['display'].lower().replace(' ', '_').replace('-', ''): key for key, value in TASK_MAPPING.items()}


@app.route('/')
def index():
    """Render the main interface."""
    return render_template('index.html', tasks=AVAILABLE_TASKS)


@app.route('/api/task-categories', methods=['GET'])
def get_task_categories():
    """Get all tasks organized by category."""
    # Maintain order: Functional, Correction, Model, System, Tasks
    category_order = ['Functional', 'Correction', 'Model', 'System', 'Tasks']
    ordered_categories = []
    
    for cat in category_order:
        if cat in TASK_CATEGORIES:
            ordered_categories.append({
                'name': cat,
                'tasks': TASK_CATEGORIES[cat]
            })
    
    return jsonify({'categories': ordered_categories})


@app.route('/api/task-params', methods=['POST'])
def get_task_params():
    """Get parameters for a selected task."""
    data = request.json
    task_name = data.get('task', '').strip()
    
    # Find the matching task in TASK_MAPPING
    task_key = None
    for key, value in TASK_MAPPING.items():
        if value['display'].lower() == task_name.lower():
            task_key = key
            break
    
    if not task_key:
        return jsonify({'error': f'Invalid task: {task_name}'}), 400
    
    params = TASK_MAPPING[task_key]['params']
    return jsonify({'params': params})


@app.route('/api/standard-params', methods=['GET'])
def get_standard_params():
    """Get all standard parameters grouped by category.
    Excludes LAPACK, NCORE, and WRITE sections as they are now System buttons."""
    # Filter out sections that are now System buttons
    filtered_standard = {
        k: v for k, v in standard_incar.items() 
        if k not in ['d_lapack', 'd_ncore', 'd_write']
    }
    return jsonify({'standard': filtered_standard})


@app.route('/api/generate-incar', methods=['POST'])
def generate_incar():
    """Generate INCAR content based on selected parameters."""
    data = request.json
    selected_tasks = data.get('tasks', [])  # Changed from 'task' to 'tasks' (list)
    custom_params = data.get('custom_params', {})
    include_sections = data.get('include_sections', {})
    
    # Track parameters by source for organized output
    task_params_by_name = {}  # Dictionary to keep params organized by task
    standard_params_by_section = {}
    final_custom_params = {}
    
    # Add selected standard parameter sections
    for section, include in include_sections.items():
        if include and section in standard_incar:
            standard_params_by_section[section] = standard_incar[section]
    
    # Separate actual Tasks from Model/System items
    actual_task_params = {}  # Parameters from Tasks category
    model_params = {}  # Parameters from Model/System/Correction categories
    selected_task_names = []
    
    for selected_task in selected_tasks:
        if selected_task:
            # Find matching task and determine its category
            task_key = None
            category = None
            for key, value in TASK_MAPPING.items():
                if value['display'].lower() == selected_task.lower():
                    task_key = key
                    category = value.get('category')
                    selected_task_names.append(value['display'])
                    break
            
            if task_key:
                params = TASK_MAPPING[task_key]['params']
                if category == 'Tasks':
                    # Store actual task parameters separately for priority
                    actual_task_params[value['display']] = params
                else:
                    # Store model/system/correction parameters
                    model_params[value['display']] = params
    
    # Build task_params_by_name with model params first, then actual task params (so tasks override)
    task_params_by_name.update(model_params)
    task_params_by_name.update(actual_task_params)
    
    # Add/override with custom parameters
    for key, value in custom_params.items():
        if key.strip():  # Only add non-empty keys
            final_custom_params[key.strip()] = value.strip()
    
    # Generate INCAR content with organized structure (separated by task)
    incar_content = _generate_incar_content_organized(
        task_params_by_name, 
        standard_params_by_section, 
        final_custom_params
    )
    
    # Count total params
    task_params_count = sum(len(v) for v in task_params_by_name.values())
    total_params = task_params_count + sum(len(v) for v in standard_params_by_section.values()) + len(final_custom_params)
    
    # Merge all params for return
    all_params = {}
    for task_params in task_params_by_name.values():
        all_params.update(task_params)
    all_params.update(final_custom_params)
    for section_params in standard_params_by_section.values():
        all_params.update(section_params)
    
    return jsonify({
        'incar_content': incar_content,
        'param_count': total_params,
        'params': all_params
    })


@app.route('/api/download-incar', methods=['POST'])
def download_incar():
    """Download INCAR file."""
    data = request.json
    incar_content = data.get('content', '')
    
    if not incar_content:
        return jsonify({'error': 'No INCAR content provided'}), 400
    
    # Create a BytesIO object with encoded content
    output = BytesIO(incar_content.encode('utf-8'))
    output.seek(0)
    
    # Send file
    return send_file(
        output,
        mimetype='text/plain',
        as_attachment=True,
        download_name='INCAR'
    )


def _generate_incar_content(params_dict):
    """Generate formatted INCAR file content."""
    lines = []
    lines.append('# INCAR file generated by Q-robot INCAR Generator')
    lines.append('')
    
    # Group parameters by category (if key contains certain prefixes)
    for key in sorted(params_dict.keys()):
        value = params_dict[key]
        lines.append(f'{key} = {value}')
    
    return '\n'.join(lines)


def _generate_incar_content_organized(task_params_by_name, standard_params_by_section, custom_params):
    """Generate organized INCAR file content with section headers for each task.
    Task parameters take precedence over standard parameters when conflicts occur.
    SYSTEM parameter always appears first and is not shown in standard sections."""
    lines = []
    # Add SYSTEM parameter at the beginning (always, not configurable)
    lines.append('SYSTEM = Generated By Q_robot')
    lines.append('')
    
    # Collect all task parameter keys to identify conflicts
    task_param_keys = set()
    if task_params_by_name:
        for params in task_params_by_name.values():
            task_param_keys.update(params.keys())
    
    # Add task parameters with separate headers for each task
    if task_params_by_name:
        for task_name, params in task_params_by_name.items():
            lines.append(f'# Task: {task_name}')
            for key in sorted(params.keys()):
                value = params[key]
                lines.append(f'{key} = {value}')
            lines.append('')
    
    # Add standard parameters grouped by section, excluding parameters that conflict with task parameters
    if standard_params_by_section:
        # Process sections - System section is skipped (SYSTEM is already at top)
        system_params = standard_params_by_section.pop('d_system', {})
        # Note: System section is deliberately not included since SYSTEM is already at the top
        
        # Add remaining sections with headers
        for section, params in sorted(standard_params_by_section.items()):
            # Filter out parameters that conflict with task parameters
            filtered_params = {k: v for k, v in params.items() if k not in task_param_keys}
            if filtered_params:
                # Format section name: d_system -> System
                section_name = section.replace('d_', '').replace('_', ' ').title()
                lines.append(f'# Standard Parameters - {section_name}')
                for key in sorted(filtered_params.keys()):
                    value = filtered_params[key]
                    lines.append(f'{key} = {value}')
                lines.append('')
    
    # Add custom parameters
    if custom_params:
        lines.append('# Custom Parameters')
        for key in sorted(custom_params.keys()):
            value = custom_params[key]
            lines.append(f'{key} = {value}')
        lines.append('')
    
    # Remove trailing empty line
    content = '\n'.join(lines).rstrip()
    return content


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@app.route('/api/read-poscar', methods=['POST'])
def read_poscar():
    """Read POSCAR file and return element information."""
    try:
        # Try importing ASE to read POSCAR
        from ase.io import read
        
        # Check multiple possible POSCAR locations
        poscar_paths = ['POSCAR', './POSCAR', '../POSCAR', '../../POSCAR']
        poscar_content = None
        
        for path in poscar_paths:
            if os.path.isfile(path):
                try:
                    atoms = read(path, format='vasp')
                    elements = atoms.get_chemical_symbols()
                    
                    # Count unique elements
                    unique_elements = []
                    element_counts = {}
                    for elem in elements:
                        if elem not in element_counts:
                            unique_elements.append(elem)
                            element_counts[elem] = 1
                        else:
                            element_counts[elem] += 1
                    
                    return jsonify({
                        'success': True,
                        'elements': unique_elements,
                        'element_counts': element_counts,
                        'total_atoms': len(elements)
                    })
                except Exception as e:
                    continue
        
        return jsonify({'success': False, 'error': 'POSCAR file not found'}), 404
    
    except ImportError:
        return jsonify({'success': False, 'error': 'ASE module not installed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/calculate-dftu', methods=['POST'])
def calculate_dftu():
    """Calculate DFT+U parameters based on POSCAR elements."""
    try:
        if not HAS_DATA_MODULE:
            return jsonify({'success': False, 'error': 'data module not available'}), 400
        
        from ase.io import read
        
        poscar_paths = ['POSCAR', './POSCAR', '../POSCAR', '../../POSCAR']
        
        for path in poscar_paths:
            if os.path.isfile(path):
                try:
                    atoms = read(path, format='vasp')
                    elements = atoms.get_chemical_symbols()
                    
                    unique_elements = []
                    ldaul, u, j = [], [], []
                    
                    for element in elements:
                        if element not in unique_elements:
                            unique_elements.append(element)
                            if element in u_value:
                                ldaul.append(2)  # Apply DFT+U to this element
                                u.append(u_value[element])
                                j.append(j_value.get(element, 0))
                            else:
                                ldaul.append(-1)  # No DFT+U applied
                                u.append(0)
                                j.append(0)
                    
                    return jsonify({
                        'success': True,
                        'LDAUL': '  '.join(map(str, ldaul)),
                        'LDAUU': '  '.join(map(str, u)),
                        'LDAUJ': '  '.join(map(str, j))
                    })
                except Exception as e:
                    continue
        
        return jsonify({'success': False, 'error': 'POSCAR file not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/calculate-magmom', methods=['POST'])
def calculate_magmom():
    """Calculate MAGMOM based on POSCAR elements."""
    try:
        if not HAS_DATA_MODULE:
            return jsonify({'success': False, 'error': 'data module not available'}), 400
        
        from ase.io import read
        
        poscar_paths = ['POSCAR', './POSCAR', '../POSCAR', '../../POSCAR']
        
        for path in poscar_paths:
            if os.path.isfile(path):
                try:
                    atoms = read(path, format='vasp')
                    symbols = atoms.get_chemical_symbols()
                    
                    element_counts = {}
                    for symbol in symbols:
                        if symbol in element_counts:
                            element_counts[symbol] += 1
                        else:
                            element_counts[symbol] = 1
                    
                    magmom_list = []
                    for symbol, count in element_counts.items():
                        magmom_per_atom = mag_value.get(symbol, 0.0)
                        magmom_list.append(f"{count}*{magmom_per_atom}")
                    
                    magmom_str = "  ".join(magmom_list)
                    
                    return jsonify({
                        'success': True,
                        'MAGMOM': magmom_str
                    })
                except Exception as e:
                    continue
        
        return jsonify({'success': False, 'error': 'POSCAR file not found'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/calculate-neb-images', methods=['POST'])
def calculate_neb_images():
    """Count NEB image folders and calculate IMAGE number."""
    try:
        # Look for folders named 00, 01, 02, etc.
        folders = [f for f in os.listdir('.') if os.path.isdir(f)]
        image_folders = [f for f in folders if f.isdigit() and len(f) == 2]
        
        if image_folders:
            image_count = len(image_folders) - 2  # Total folders minus initial and final
            if image_count < 0:
                image_count = 0
            
            return jsonify({
                'success': True,
                'IMAGES': str(image_count),
                'folder_count': len(image_folders)
            })
        else:
            return jsonify({'success': False, 'error': 'No image folders found (00, 01, 02...)'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
