# Autonomous-Mobile-Bot

This repository contains the ROS2 software stack for a custom-built, autonomous mobile robot. The project integrates a Raspberry Pi for high-level processing (Slam, Navigation, Perception) and an Arduino for low-level motor control and odometry.

## 🤖 Features
* **ROS2 Middleware:** Developed and tested using ROS2 (Humble/Foxy).
* **SLAM & Navigation:** Integrated with `slam_toolbox` for real-time mapping and the `Nav2` stack for autonomous path planning.
* **Hardware Bridge:** Features a custom `arduino_bridge` node that handles serial communication between the Raspberry Pi and the Arduino microcontroller.
* **Sensor Fusion:** Supports LiDAR data via `urg_node2` and IMU data from an MPU6050 for accurate localization.
* **Digital Twin:** Includes a detailed URDF (Xacro) model for visualization in RViz and simulation in Gazebo.

## 🏗 Repository Structure
* **`arduino_bridge_new`**: Python node managing serial communication, wheel velocity commands, and odometry calculation.
* **`bot_bringup`**: Central launch files for hardware configuration and system localization.
* **`bot_controller`**: Implements a simple controller to translate `Twist` messages into individual wheel commands.
* **`bot_description`**: Contains the URDF models, meshes, and Gazebo simulation parameters.
* **`bot_localization`**: Extended Kalman Filter (EKF) configurations for sensor fusion.
* **`turtlebot_navigation`**: Navigation and SLAM parameters specifically tuned for the mobile bot.
* **`imu_mpu6050`**: Driver node for the MPU6050 Inertial Measurement Unit.
* **`urg_node2`**: Driver for Hokuyo URG LiDAR sensors.

## 🛠 Hardware Setup
* **Compute:** Raspberry Pi (Running ROS2).
* **Microcontroller:** Arduino (Motor Control & Encoders).
* **Lidar:** Hokuyo URG Series (or compatible).
* **IMU:** MPU6050.
* **Chassis:** Small-scale Turtlebot-style differential drive.

## 🚀 Installation & Usage
1.  **Clone the workspace:**
    ```bash
    mkdir -p ~/bot_ws/src
    cd ~/bot_ws/src
    git clone [https://github.com/yenode/Autonomous-Mobile-Bot.git](https://github.com/yenode/Autonomous-Mobile-Bot.git)
    ```
2.  **Install dependencies:**
    ```bash
    cd ~/bot_ws
    rosdep install --from-paths src --ignore-src -r -y
    ```
3.  **Build and Source:**
    ```bash
    colcon build --symlink-install
    source install/setup.bash
    ```
4.  **Launch the robot:**
    ```bash
    ros2 launch bot_bringup hardware_configure.launch.xml
    ```

## 🤝 Credits
* **Software & ROS2 Integration:** Yenode
* **Hardware Design & Management:** [Friend's Name] — *Special thanks for managing the physical assembly and hardware configuration.*

## 📜 License
This project is licensed under the MIT License.
