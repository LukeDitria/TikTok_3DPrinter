#!/bin/bash

echo "🚀 Setting up TikTok 3D Printer Controller..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install required packages from requirements.txt
echo "Installing required packages..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Check for config file
if [ ! -f "config.json" ]; then
    echo "⚙️ Setting up configuration..."
    echo "What is your TikTok username? (include the @ symbol)"
    read tiktok_username

    # Replace the username in the config file
    sed "s/@lukeditria/$tiktok_username/" config.json.template > config.json

    echo "🔍 Looking for connected printers..."
    echo "Available ports:"
    ls /dev/ttyUSB* 2>/dev/null || ls /dev/ttyACM* 2>/dev/null || echo "No printers found, please connect your printer"
    echo "Enter your printer's port (e.g., /dev/ttyUSB0):"
    read printer_port

    # Update printer port in config
    sed -i "s|/dev/ttyUSB0|$printer_port|" config.json
fi

chmod +x run.sh
echo "✅ Setup complete!"
