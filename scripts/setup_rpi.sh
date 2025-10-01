#!/bin/bash

# Raspberry Pi Setup Script for Arduino Bridge
echo "Setting up Raspberry Pi for Arduino communication..."

# Add user to dialout group for serial access
echo "Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Install required Python packages
echo "Installing Python dependencies..."
pip3 install pyserial

# Set up udev rules for consistent Arduino device naming
echo "Setting up udev rules for Arduino..."
sudo tee /etc/udev/rules.d/99-arduino.rules > /dev/null <<EOF
# Arduino Uno/Nano (FTDI)
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", SYMLINK+="arduino_ftdi"

# Arduino Uno R3 (ATmega16U2)
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="0043", SYMLINK+="arduino_uno"

# Arduino Nano (CH340)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="arduino_nano"

# Generic Arduino compatible
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", SYMLINK+="arduino"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Check for Arduino devices
echo "Checking for Arduino devices..."
ls -la /dev/tty* | grep -E "(ACM|USB)"

echo "Setup complete!"
echo "Please log out and log back in for group changes to take effect."
echo ""
echo "To test Arduino connection:"
echo "  ls /dev/tty* | grep -E '(ACM|USB)'"
echo "  dmesg | tail -20  # Check for USB device messages"
echo ""
echo "Common Arduino ports on Raspberry Pi:"
echo "  /dev/ttyACM0  - Arduino Uno R3"
echo "  /dev/ttyUSB0  - Arduino with FTDI/CH340 chip"
