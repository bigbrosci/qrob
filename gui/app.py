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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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

# Add custom tasks
CUSTOM_TASKS = {
    'B3LYP-Hybrid': {
        'display': 'B3LYP-Hybrid',
        'params': {
            'LHFCALC': 'T',
            'AEXX': '0.20',
            'AGGAC': '0.81',
            'AGGAX': '0.72',
            'ALDAC': '0.19',
            'GGA': 'B3'
        }
    },
    'Electronic-Properties': {
        'display': 'Electronic-Properties',
        'params': {
            'LAECHG': 'T',
            'LCHARG': 'T',
            'LELF': 'T',
            'LORBIT': '11',
            'LWAVE': 'T',
            'NEDOS': '1000'
        }
    },
    'MD-Simulation': {
        'display': 'MD-Simulation',
        'params': {
            'IBRION': '0',
            'MDALGO': '2',
            'NBLOCK': '5',
            'NSW': '50000',
            'POTIM': '1',
            'SMASS': '0',
            'TEBEG': '273',
            'TEEND': '273'
        }
    }
}

# Merge custom tasks with imported tasks
for custom_key, custom_task in CUSTOM_TASKS.items():
    TASK_MAPPING[custom_key] = custom_task

AVAILABLE_TASKS = [TASK_MAPPING[key]['display'] for key in sorted(TASK_MAPPING.keys())]
TASK_KEYS = {value['display'].lower().replace(' ', '_').replace('-', ''): key for key, value in TASK_MAPPING.items()}


@app.route('/')
def index():
    """Render the main interface."""
    return render_template('index.html', tasks=AVAILABLE_TASKS)


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
    """Get all standard parameters grouped by category."""
    return jsonify({'standard': standard_incar})


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
    
    # Add task parameters from all selected tasks (keep them separate)
    selected_task_names = []
    for selected_task in selected_tasks:
        if selected_task:
            # Find matching task
            task_key = None
            for key, value in TASK_MAPPING.items():
                if value['display'].lower() == selected_task.lower():
                    task_key = key
                    selected_task_names.append(value['display'])
                    break
            
            if task_key:
                task_params_by_name[value['display']] = TASK_MAPPING[task_key]['params']
    
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
    """Generate organized INCAR file content with section headers for each task."""
    lines = []
    # Add SYSTEM parameter at the beginning
    lines.append('SYSTEM = Generated By Q_robot')
    lines.append('')
    
    # Add task parameters with separate headers for each task
    if task_params_by_name:
        for task_name, params in task_params_by_name.items():
            lines.append(f'# Task: {task_name}')
            for key in sorted(params.keys()):
                value = params[key]
                lines.append(f'{key} = {value}')
            lines.append('')
    
    # Add standard parameters grouped by section
    if standard_params_by_section:
        # Process sections - System goes first without section header
        system_params = standard_params_by_section.pop('d_system', {})
        if system_params:
            # Add system params at the beginning (right after task params)
            for key in sorted(system_params.keys()):
                value = system_params[key]
                lines.append(f'{key} = {value}')
            lines.append('')
        
        # Add remaining sections with headers
        for section, params in sorted(standard_params_by_section.items()):
            # Format section name: d_system -> System
            section_name = section.replace('d_', '').replace('_', ' ').title()
            lines.append(f'# Standard Parameters - {section_name}')
            for key in sorted(params.keys()):
                value = params[key]
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


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
