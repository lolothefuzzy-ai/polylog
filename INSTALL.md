# Polylog Installation Guide

## Requirements
- Python 3.10+
- Git

## Setup
```bash
git clone https://github.com/lolothefuzzy-ai/polylog.git
cd polylog
python launcher.py
```

The launcher will automatically:
1. Create a virtual environment
2. Install dependencies
3. Prompt for mode selection (GUI/API/Demo)

## Manual Setup (Advanced)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python Properties/Code/main.py [gui|api|demo]
```

## Running

### GUI Mode
```bash
python Properties/Code/main.py gui
```

### API Mode
```bash
python Properties/Code/main.py api
```

### Troubleshooting
- **GUI Dependencies**: If GUI fails, install PyQt5 manually:
```bash
pip install PyQt5==5.15.10
```
- **API Issues**: Ensure the root directory contains `polylog_main.py`
