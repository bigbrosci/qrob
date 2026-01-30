# Q-robot INCAR Generator Web Interface

A modern, user-friendly web interface for generating VASP INCAR files using the Q-robot framework.

## Features

- **Interactive Task Selection**: Choose from 20+ pre-configured calculation tasks
- **Standard Parameters**: Organize and select from standard parameter groups
- **Custom Parameters**: Add your own parameters on the fly
- **Live Preview**: See your INCAR file as you configure it
- **One-Click Download**: Export your INCAR file directly
- **Copy to Clipboard**: Quick copying for pasting into your workflow
- **Responsive Design**: Works on desktop and tablet devices

## Available Calculation Tasks

- Single point calculations
- Density of State (DOS)
- Electronic structure analysis
- Work function calculations
- Molecular Dynamics (MD)
- Gas phase calculations
- Bulk structure optimizations
- DFT+U calculations
- Dipole moment calculations
- Transition State Optimization (TS-OPT)
- Nudged Elastic Band (NEB)
- Dimer method
- Vibrational frequencies
- Van der Waals (vdW) corrections (D3, D3-BJ)
- Machine Learning (ML) methods
- Hybrid functional calculations (PBE0, HSE03, HSE06, B3LYP, HF)

## Installation

### Prerequisites
- Python 3.7+
- Flask
- The Q-robot brain module (parent directory)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage Workflow

1. **Select a Task**: Click on one of the calculation task buttons to load task-specific parameters
2. **Choose Standard Parameters**: Check the boxes for standard parameter sections you want to include
3. **Add Custom Parameters**: Use the custom parameters section to add or override any parameters
4. **Generate INCAR**: Click "Generate INCAR" to preview the file
5. **Download or Copy**: 
   - Click "Download INCAR File" to save it locally
   - Click "Copy to Clipboard" to paste it elsewhere
   - Click "Reset Form" to start over

## File Structure

```
gui/
├── app.py                 # Flask application backend
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main web interface
└── static/
    ├── css/
    │   └── style.css     # Styling and layout
    └── js/
        └── main.js       # Frontend logic and interactions
```

## API Endpoints

- `GET /` - Main interface page
- `POST /api/standard-params` - Get all standard parameters
- `POST /api/task-params` - Get parameters for a specific task
- `POST /api/generate-incar` - Generate INCAR content
- `POST /api/download-incar` - Download INCAR file
- `GET /health` - Health check

## Customization

### Adding New Tasks

To add a new calculation task:

1. Edit the `incar.py` module in the brain folder
2. Add a new entry to `tasks_incar` dictionary with key `d_cal_yourtaskname`
3. The GUI will automatically include it in the task selection

### Modifying Standard Parameters

Edit the `standard_incar` dictionary in `incar.py` to change or add standard parameter groups.

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify the `app.py` file:
```python
app.run(debug=True, host='127.0.0.1', port=5001)  # Change 5000 to another port
```

### Brain Module Not Found
Ensure the `brain` folder is in the parent directory of the `gui` folder.

### CSS/JS Not Loading
- Clear browser cache
- Check that static files are in the correct directories
- Verify Flask can access the static files

## Development

To run in development mode with auto-reload:
```bash
python app.py
```

The Flask development server will automatically reload when you modify any Python files.

## Production Deployment

For production deployment, consider using:
- Gunicorn instead of Flask's development server
- Nginx as a reverse proxy
- Environment variables for configuration

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## License

This interface is part of the Q-robot project.

## Support

For issues or questions about the INCAR Generator interface, refer to the Q-robot documentation or contact the development team.
