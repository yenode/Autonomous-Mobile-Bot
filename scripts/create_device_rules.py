#!/usr/bin/env python3

import subprocess
import os
import sys
import serial.tools.list_ports

def get_device_info():
    """Get detailed information about connected USB serial devices"""
    print("🔍 Scanning for USB serial devices...")
    
    ports = serial.tools.list_ports.comports()
    devices = []
    
    for port in ports:
        if port.device.startswith('/dev/ttyACM') or port.device.startswith('/dev/ttyUSB'):
            print(f"\n Found device: {port.device}")
            print(f"   Description: {port.description}")
            
            device_info = {
                'device': port.device,
                'description': port.description,
                'vid': None,
                'pid': None,
                'serial': None,
                'manufacturer': None,
                'product': None
            }
            
            if hasattr(port, 'vid') and port.vid:
                device_info['vid'] = f"{port.vid:04x}"
                print(f"   VID: {device_info['vid']}")
            
            if hasattr(port, 'pid') and port.pid:
                device_info['pid'] = f"{port.pid:04x}"
                print(f"   PID: {device_info['pid']}")
            
            if hasattr(port, 'serial_number') and port.serial_number:
                device_info['serial'] = port.serial_number
                print(f"   Serial: {device_info['serial']}")
            
            if hasattr(port, 'manufacturer') and port.manufacturer:
                device_info['manufacturer'] = port.manufacturer
                print(f"   Manufacturer: {device_info['manufacturer']}")
            
            if hasattr(port, 'product') and port.product:
                device_info['product'] = port.product
                print(f"   Product: {device_info['product']}")
            
            # Get additional udev info
            try:
                result = subprocess.run(['udevadm', 'info', '--name=' + port.device, '--query=property'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'ID_SERIAL_SHORT=' in line:
                            device_info['serial'] = line.split('=')[1]
                        elif 'ID_VENDOR_ID=' in line:
                            device_info['vid'] = line.split('=')[1]
                        elif 'ID_MODEL_ID=' in line:
                            device_info['pid'] = line.split('=')[1]
            except:
                pass
            
            devices.append(device_info)
    
    return devices

def identify_device_type(device_info):
    """Try to identify if device is Arduino or Hokuyo URG"""
    desc = device_info['description'].lower()
    manufacturer = (device_info['manufacturer'] or '').lower()
    product = (device_info['product'] or '').lower()
    
    # Check for Hokuyo URG
    if any(keyword in desc for keyword in ['hokuyo', 'urg']) or \
       any(keyword in manufacturer for keyword in ['hokuyo']) or \
       any(keyword in product for keyword in ['urg', 'hokuyo']) or \
       device_info['vid'] == '15d1':  # Hokuyo VID
        return 'hokuyo_urg'
    
    # Check for Arduino
    if any(keyword in desc for keyword in ['arduino', 'uno', 'nano', 'mega']) or \
       any(keyword in manufacturer for keyword in ['arduino']) or \
       any(keyword in product for keyword in ['arduino']) or \
       device_info['vid'] in ['2341', '1a86', '0403']:  # Common Arduino VIDs
        return 'arduino'
    
    # Check for common USB-serial chips used by Arduino
    if any(keyword in desc for keyword in ['ch340', 'cp210', 'ftdi', 'usb serial']) or \
       device_info['vid'] in ['1a86', '10c4', '0403']:  # CH340, CP210x, FTDI
        return 'arduino_compatible'
    
    return 'unknown'

def create_udev_rules(devices):
    """Create udev rules for persistent device naming"""
    rules = []
    rules.append('# Persistent device names for TurtleBot')
    rules.append('# Created by create_device_rules.py')
    rules.append('')
    
    for i, device in enumerate(devices):
        device_type = identify_device_type(device)
        
        if device_type == 'hokuyo_urg':
            symlink_name = 'ttyHOKUYO'
            comment = f"# Hokuyo URG LiDAR"
        elif device_type in ['arduino', 'arduino_compatible']:
            symlink_name = 'ttyARDUINO'
            comment = f"# Arduino or compatible device"
        else:
            symlink_name = f'ttyUNKNOWN{i}'
            comment = f"# Unknown device {i}"
        
        rules.append(comment)
        
        # Create rule based on available identifiers
        rule_parts = []
        
        if device['vid'] and device['pid']:
            rule_parts.append(f'ATTRS{{idVendor}}=="{device["vid"]}", ATTRS{{idProduct}}=="{device["pid"]}"')
        elif device['vid']:
            rule_parts.append(f'ATTRS{{idVendor}}=="{device["vid"]}"')
        
        if device['serial']:
            rule_parts.append(f'ATTRS{{serial}}=="{device["serial"]}"')
        
        if rule_parts:
            rule = f'SUBSYSTEM=="tty", {", ".join(rule_parts)}, SYMLINK+="{symlink_name}"'
            rules.append(rule)
        else:
            rules.append(f'# Could not create rule for {device["device"]} - insufficient identifiers')
        
        rules.append('')
    
    return '\n'.join(rules)

def main():
    print(" TurtleBot Device Rules Creator")
    print("=" * 50)
    print("This script will help create persistent device names for your Arduino and Hokuyo URG")
    print()
    
    # Check if running as root for udev rule creation
    if os.geteuid() != 0:
        print("  Note: You'll need sudo privileges to install the udev rules")
    
    # Get device information
    devices = get_device_info()
    
    if not devices:
        print("\n No USB serial devices found!")
        print("Please connect your Arduino and/or Hokuyo URG and run this script again.")
        return
    
    print(f"\n Found {len(devices)} USB serial device(s)")
    
    # Identify devices
    for device in devices:
        device_type = identify_device_type(device)
        print(f"\n {device['device']}: Identified as '{device_type}'")
    
    # Create udev rules
    rules_content = create_udev_rules(devices)
    
    print("\n Generated udev rules:")
    print("=" * 50)
    print(rules_content)
    print("=" * 50)
    
    # Save rules to file
    rules_file = '/tmp/99-turtlebot-devices.rules'
    with open(rules_file, 'w') as f:
        f.write(rules_content)
    
    print(f"\n Rules saved to: {rules_file}")
    
    # Provide installation instructions
    print("\n To install these rules:")
    print(f"1. sudo cp {rules_file} /etc/udev/rules.d/")
    print("2. sudo udevadm control --reload-rules")
    print("3. sudo udevadm trigger")
    print("4. Disconnect and reconnect your devices")
    print()
    print("After installation, your devices will be available as:")
    
    for device in devices:
        device_type = identify_device_type(device)
        if device_type == 'hokuyo_urg':
            print(f"    Hokuyo URG: /dev/ttyHOKUYO")
        elif device_type in ['arduino', 'arduino_compatible']:
            print(f"    Arduino: /dev/ttyARDUINO")
    
    print()
    print(" Auto-install rules? (requires sudo)")
    response = input("Install now? (y/N): ").strip().lower()
    
    if response == 'y':
        try:
            subprocess.run(['sudo', 'cp', rules_file, '/etc/udev/rules.d/'], check=True)
            subprocess.run(['sudo', 'udevadm', 'control', '--reload-rules'], check=True)
            subprocess.run(['sudo', 'udevadm', 'trigger'], check=True)
            print(" Rules installed successfully!")
            print(" Please disconnect and reconnect your devices to activate the new names.")
        except subprocess.CalledProcessError as e:
            print(f" Failed to install rules: {e}")
        except KeyboardInterrupt:
            print("\n Installation cancelled")

if __name__ == "__main__":
    main()
