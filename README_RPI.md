# Arduino Bridge for Raspberry Pi

This package provides ROS2 integration with Arduino for motor control on Raspberry Pi.

## 🔧 Raspberry Pi Setup

### 1. Initial Setup
```bash
# Run the setup script
chmod +x scripts/setup_rpi.sh
./scripts/setup_rpi.sh

# Log out and log back in for group changes to take effect
```

### 2. Find Your Arduino
```bash
# List available serial ports
ls /dev/tty* | grep -E "(ACM|USB)"

# Check USB device messages
dmesg | tail -20

# Run diagnostic tool
ros2 run arduino_bridge diagnose_arduino
```

### 3. Common Arduino Ports on Raspberry Pi
- `/dev/ttyACM0` - Arduino Uno R3 (most common)
- `/dev/ttyUSB0` - Arduino with FTDI/CH340 chip
- `/dev/ttyACM1` - Second Arduino device

## 🚀 Usage

### Launch Arduino Bridge
```bash
# Basic launch (auto-detects Arduino port)
ros2 launch arduino_bridge arduino_bridge.launch.py

# Specify custom port
ros2 launch arduino_bridge arduino_bridge.launch.py serial_port:=/dev/ttyACM0

# Complete system with wheel velocity conversion
ros2 launch arduino_bridge complete_bridge.launch.py
```

### Send Commands

#### Option 1: Direct Wheel Velocities
```bash
# Send wheel velocities directly (rad/s)
ros2 topic pub /wheel_velocities std_msgs/msg/Float64MultiArray "data: [2.0, -2.0]"
```

#### Option 2: Twist Messages (Auto-converted)
```bash
# Use teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args --remap cmd_vel:=/bot_controller/cmd_vel

# Or publish directly
ros2 topic pub /bot_controller/cmd_vel geometry_msgs/msg/Twist "linear: {x: 0.5}, angular: {z: 0.3}"
```

## 📊 Message Flow

```
Twist (/bot_controller/cmd_vel) → wheel_velocity_publisher → Float64MultiArray (/wheel_velocities) → arduino_bridge → Arduino
```

## 🔍 Troubleshooting

### Arduino Not Found
```bash
# Check if Arduino is connected
lsusb | grep -i arduino

# Check permissions
groups $USER  # Should include 'dialout'

# Run diagnostic
ros2 run arduino_bridge diagnose_arduino
```

### Connection Issues
```bash
# Check for device conflicts
sudo fuser /dev/ttyACM0  # Replace with your port

# Reset USB subsystem
sudo modprobe -r usbserial
sudo modprobe usbserial
```

### Serial Permission Denied
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and log back in
```

## ⚙️ Configuration

### Parameters
- `serial_port`: Arduino port (default: `/dev/ttyACM0`)
- `baud_rate`: Communication speed (default: `115200`)
- `serial_timeout`: Read timeout (default: `1.0` seconds)
- `reconnect_attempts`: Auto-reconnect tries (default: `5`)
- `wheel_radius`: Robot wheel radius (default: `0.027` m)
- `wheel_separation`: Distance between wheels (default: `0.16` m)

### Launch Arguments
```bash
ros2 launch arduino_bridge complete_bridge.launch.py \
  serial_port:=/dev/ttyACM0 \
  baud_rate:=115200 \
  wheel_radius:=0.027 \
  wheel_separation:=0.16
```

## 🔄 Auto-Reconnection Features

The bridge automatically:
- ✅ Detects Arduino disconnection
- ✅ Attempts reconnection with retry logic
- ✅ Tries multiple common ports
- ✅ Handles USB cable unplugging/replugging
- ✅ Logs connection status

## 📈 Monitoring

```bash
# Monitor Arduino communication
ros2 topic echo /odom

# Check joint states
ros2 topic echo /joint_states

# Monitor wheel velocities
ros2 topic echo /wheel_velocities
```

## 🐛 Debug Mode

```bash
# Enable debug logging
ros2 launch arduino_bridge arduino_bridge.launch.py --ros-args --log-level DEBUG
```
