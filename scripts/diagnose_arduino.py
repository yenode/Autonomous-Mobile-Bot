#!/usr/bin/env python3

import serial
import serial.tools.list_ports
import time

def list_serial_ports():
    """List all available serial ports"""
    print("Available serial ports:")
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("  No serial ports found!")
        return []
    
    for port in ports:
        print(f"  {port.device} - {port.description}")
        if hasattr(port, 'vid') and hasattr(port, 'pid') and port.vid is not None and port.pid is not None:
            print(f"    VID:PID = {port.vid:04X}:{port.pid:04X}")
    
    return [port.device for port in ports]

def test_arduino_connection(port, baud_rate=115200):
    """Test connection to Arduino"""
    print(f"\nTesting connection to {port} at {baud_rate} baud...")
    
    try:
        # Open serial connection
        ser = serial.Serial(port, baud_rate, timeout=2)
        time.sleep(3)  # Wait for Arduino to initialize
        
        print(f"  ✓ Successfully opened {port}")
        print(f"  ✓ Port is open: {ser.is_open}")
        
        # Try to read any data
        if ser.in_waiting > 0:
            data = ser.readline().decode().strip()
            print(f"  ✓ Received data: {data}")
        else:
            print("  ⚠ No data available to read")
        
        # Try to send a test command
        test_cmd = "0.0,0.0\n"
        ser.write(test_cmd.encode())
        print(f"  ✓ Sent test command: {test_cmd.strip()}")
        
        # Wait for response
        time.sleep(0.5)
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"  ✓ Arduino response: {response}")
        else:
            print("  ⚠ No response from Arduino")
        
        ser.close()
        print(f"  ✓ Connection test completed successfully")
        return True
        
    except serial.SerialException as e:
        print(f"  ✗ Serial error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

def check_permissions():
    """Check if user has permission to access serial ports"""
    import os
    import grp
    
    print("\nChecking permissions...")
    
    # Check if user is in dialout group
    try:
        dialout_group = grp.getgrnam('dialout')
        current_user = os.getenv('USER')
        
        if current_user in dialout_group.gr_mem:
            print(f"  ✓ User '{current_user}' is in dialout group")
        else:
            print(f"  ✗ User '{current_user}' is NOT in dialout group")
            print("    Run: sudo usermod -a -G dialout $USER")
            print("    Then log out and log back in")
    except KeyError:
        print("  ⚠ dialout group not found")

def main():
    print("Arduino Connection Diagnostic Tool")
    print("=" * 40)
    
    # Check permissions
    check_permissions()
    
    # List available ports
    available_ports = list_serial_ports()
    
    if not available_ports:
        print("\nNo serial ports found. Check if Arduino is connected.")
        return
    
    # Test common Arduino ports
    common_ports = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    print(f"\nTesting common Arduino ports...")
    for port in common_ports:
        if port in available_ports:
            if test_arduino_connection(port):
                print(f"\n🎉 Arduino found and working on {port}")
                break
        else:
            print(f"  ⚠ {port} not available")
    
    # Test all available ports if common ones failed
    print(f"\nTesting all available ports...")
    for port in available_ports:
        if port not in common_ports:
            test_arduino_connection(port)
    
    print("\nDiagnostic complete!")
    print("\nTroubleshooting tips:")
    print("1. Make sure Arduino is connected via USB")
    print("2. Check that Arduino code is uploaded and running")
    print("3. Verify user is in dialout group")
    print("4. Try different USB ports/cables")
    print("5. Check dmesg for USB connection messages: dmesg | tail -20")

if __name__ == "__main__":
    main()
