#!/bin/bash
# Activate the virtual environment if required
source venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

playwright install
# Run the Python script
python3 main.py