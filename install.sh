#!/bin/bash
# Raspberry Pi Audio Monitor Installation Script

echo "Installing Electrical Panel Audio Monitor..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip portaudio19-dev python3-dev git

# Install Python packages
pip3 install pyaudio numpy scipy

# Create recordings directory
mkdir -p recordings

# Set permissions
chmod +x electrical_panel_monitor.py

echo "Installation complete!"
echo "To start monitoring, run: python3 electrical_panel_monitor.py"
