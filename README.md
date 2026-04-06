# Autonomous-Mobile-Bot

This repository contains the ROS2 software stack for a custom-built mobile robot. The project integrates a Raspberry Pi for high-level processing and an Arduino for low-level motor control and odometry data.

## Overview
The system is designed as a small-scale mobile platform using a differential drive configuration. It currently supports manual movement and real-time data acquisition from a LiDAR sensor. The software architecture is modular, allowing for future implementation of autonomous navigation and SLAM.

## Features
* ROS2 Middleware: Built and organized using ROS2 packages.
* Hardware Bridge: A custom Python-based serial bridge (arduino_bridge) translates ROS wheel_velocities into hardware-level commands.
* Sensor Integration: Real-time data streaming from a LiDAR sensor via the urg_node2 driver.
* Digital Twin: Comprehensive URDF/Xacro models for robot visualization and transform (TF) broadcasting.

## Repository Structure
* arduino_bridge_new: Manages serial communication, wheel velocity commands, and odometry calculations.
* bot_bringup: Contains central launch files for hardware configuration and localization.
* bot_controller: Implements a simple controller node to handle movement logic.
* bot_description: Holds the URDF models, 3D meshes (STL/DAE), and visualization configs.
* bot_localization: Configured for sensor fusion, including IMU republishing and Kalman filtering.
* imu_mpu6050: Driver node for the MPU6050 Inertial Measurement Unit.
* urg_node2: Driver for Hokuyo URG LiDAR sensors.
* turtlebot_navigation: Package reserved for future SLAM and Nav2 configurations.

## Hardware Setup
* Compute: Raspberry Pi.
* Microcontroller: Arduino (Motor control and encoder feedback).
* Lidar: Hokuyo URG Series (connected via USB/Serial).
* Chassis: Differential drive mobile base.

## Media
### Photos
| Robot Hardware | Side View |
| :---: | :---: |
| ![WhatsApp Image 2026-03-01 at 4 45 31 PM](https://github.com/user-attachments/assets/83b990dd-91b2-493c-9edf-6e2a1f083955) | ![WhatsApp Image 2026-03-01 at 4 45 30 PM](https://github.com/user-attachments/assets/25073b87-7454-4bdc-bb08-af28468686b2)

### Videos
* Manual Robot Movement


https://github.com/user-attachments/assets/3480f9b8-0bf2-4e1f-824a-bbb08dbd436a



* LiDAR Data Visualization
  

https://github.com/user-attachments/assets/4bc2fa6a-4018-40ff-a373-498e71035544



## Installation
1. Clone the workspace:
```bash
git clone https://github.com/yenode/Autonomous-Mobile-Bot.git
```

2. Install dependencies:
```bash
rosdep install --from-paths src --ignore-src -r -y
```

3. Build the workspace:
```bash
colcon build --symlink-install
source install/setup.bash
```

## Usage
1. Launch the hardware bridge:
```bash
ros2 launch arduino_bridge_new arduino_bridge_persistent.launch.py
```

2. Bring up the LiDAR sensor:
```bash
ros2 launch urg_node2 urg_node2_persistent.launch.py
```

3. Launch the central hardware configuration:
```bash
ros2 launch bot_bringup hardware_configure.launch.xml
```
## Credits
* Software & ROS2 Integration: yenode
* Hardware Design & Management: [hexwolff](https://github.com/hexwolff)

## License
This project is licensed under the MIT License.


