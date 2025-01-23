#!/bin/bash

# Project setup script
PROJECT_DIR=$(pwd)  # Get the current working directory
VENV_DIR="venv"     # Name of the virtual environment directory
REQUIREMENTS_FILE="requirements.txt"  # Name of the requirements file

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install it and try again."
    exit 1
fi

# Create the virtual environment
echo "Creating a virtual environment in '$PROJECT_DIR/$VENV_DIR'..."
python3 -m venv $VENV_DIR

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Check if requirements.txt exists
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from '$REQUIREMENTS_FILE'..."
    pip install --upgrade pip
    pip install -r $REQUIREMENTS_FILE
else
    echo "No '$REQUIREMENTS_FILE' file found. Skipping dependency installation."
fi

# Deactivate the virtual environment
deactivate

echo "Setup complete! To activate the virtual environment, run:"
echo "source $PROJECT_DIR/$VENV_DIR/bin/activate"
