#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from tf_transformations import quaternion_from_euler
import serial
import threading
import time
import math
from typing import Optional

class ArduinoBridge(Node):
    def __init__(self):
        super().__init__('arduino_bridge')
        
        # Parameters optimized for Raspberry Pi
        self.declare_parameter('serial_port', '/dev/ttyACM0')  # Common for Arduino on RPi
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('serial_timeout', 1.0)
        self.declare_parameter('reconnect_attempts', 5)
        self.declare_parameter('wheel_radius', 0.033)  # meters
        self.declare_parameter('wheel_separation', 0.175)  # meters
        
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value
        self.serial_timeout = self.get_parameter('serial_timeout').value
        self.reconnect_attempts = self.get_parameter('reconnect_attempts').value
        if self.baud_rate is None:
            self.baud_rate = 115200  # fallback to default if None
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        
        
        # Initialize serial connection with Raspberry Pi optimizations
        self.arduino: Optional[serial.Serial] = None
        self.connect_to_arduino()
        
        # ROS2 Publishers
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.joint_pub = self.create_publisher(JointState, 'joint_states', 10)
        
        # ROS2 Subscribers
        # self.cmd_vel_sub = self.create_subscription(
        #     Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.wheel_vel_sub = self.create_subscription(
            Float64MultiArray, 'wheel_velocities', self.wheel_vel_callback, 10)
        
        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Odometry variables
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()
        
        # Wheel velocities
        self.right_wheel_vel = 0.0
        self.left_wheel_vel = 0.0
        
        # Start serial reading thread
        self.serial_thread = threading.Thread(target=self.read_serial_data)
        self.serial_thread.daemon = True
        self.serial_thread.start()
        
        # Timer for publishing odometry
        self.create_timer(0.05, self.publish_odometry)  # 20Hz
        
        self.get_logger().info('Arduino Bridge Node Started')

    def connect_to_arduino(self) -> bool:
        """Connect to Arduino with retry logic for Raspberry Pi"""
        if self.reconnect_attempts is None:
            self.reconnect_attempts = 5  # fallback to default if None
        for attempt in range(self.reconnect_attempts):
            try:
                # Try common Arduino ports on Raspberry Pi
                possible_ports = [self.serial_port, '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']

                for port in possible_ports:
                    try:
                        self.get_logger().info(f'Attempting to connect to {port}...')
                        if self.baud_rate is None:
                            self.baud_rate = 115200  # fallback to default if None
                        self.arduino = serial.Serial(port, self.baud_rate, timeout=self.serial_timeout)
                        time.sleep(3)  # Wait for Arduino to initialize (important on RPi)

                        # Test connection
                        if self.arduino.is_open:
                            self.serial_port = port  # Update to working port
                            self.get_logger().info(f'Successfully connected to Arduino on {port}')
                            return True
                    except Exception as port_error:
                        self.get_logger().debug(f'Failed to connect to {port}: {port_error}')
                        continue

                self.get_logger().warning(f'Connection attempt {attempt + 1}/{self.reconnect_attempts} failed')
                time.sleep(2)  # Wait before retry

            except Exception as e:
                self.get_logger().error(f'Connection attempt {attempt + 1} failed: {e}')
                time.sleep(2)

        self.get_logger().error('Failed to connect to Arduino after all attempts')
        return False

    def is_arduino_connected(self) -> bool:
        """Check if Arduino is connected"""
        return self.arduino is not None and self.arduino.is_open

    def reconnect_arduino(self) -> bool:
        """Attempt to reconnect to Arduino"""
        if self.arduino:
            try:
                self.arduino.close()
            except:
                pass
        self.arduino = None
        return self.connect_to_arduino()

    # def cmd_vel_callback(self, msg):
    #     """Convert twist to wheel velocities and send to Arduino"""
    #     if not self.is_arduino_connected():
    #         self.get_logger().warning('Arduino not connected, attempting reconnection...')
    #         if not self.reconnect_arduino():
    #             return

    #     try:
    #         # Convert twist to wheel velocities using differential drive kinematics
    #         right_wheel_vel = (msg.linear.x + (msg.angular.z * self.wheel_separation / 2.0)) / self.wheel_radius
    #         left_wheel_vel = (msg.linear.x - (msg.angular.z * self.wheel_separation / 2.0)) / self.wheel_radius

    #         # Send wheel velocities to Arduino
    #         command = f"{right_wheel_vel:.3f},{left_wheel_vel:.3f}\n"
    #         if self.arduino is not None:
    #             self.arduino.write(command.encode())
    #     except Exception as e:
    #         self.get_logger().error(f'Failed to send command to Arduino: {e}')
    #         self.arduino = None  # Mark as disconnected

    def wheel_vel_callback(self, msg):
        """Send wheel velocities directly to Arduino"""
        if not self.is_arduino_connected():
            self.get_logger().warning('Arduino not connected, attempting reconnection...')
            if not self.reconnect_arduino():
                return

        try:
            if len(msg.data) >= 2:
                right_wheel_vel = msg.data[0]  # rad/s
                left_wheel_vel = msg.data[1]   # rad/s

                # Send wheel velocities to Arduino
                command = f"{right_wheel_vel:.3f},{left_wheel_vel:.3f}\n"
                if self.arduino is not None:
                    self.arduino.write(command.encode())
        except Exception as e:
            self.get_logger().error(f'Failed to send wheel velocities to Arduino: {e}')
            self.arduino = None  # Mark as disconnected
    
    def read_serial_data(self):
        """Read wheel velocities from Arduino"""
        while rclpy.ok():
            try:
                if self.is_arduino_connected() and self.arduino is not None and self.arduino.in_waiting > 0:
                    line = self.arduino.readline().decode().strip()
                    if ',' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            self.right_wheel_vel = float(parts[0])
                            self.left_wheel_vel = float(parts[1])
                elif not self.is_arduino_connected():
                    # Try to reconnect if disconnected
                    self.get_logger().debug('Arduino disconnected, attempting reconnection...')
                    self.reconnect_arduino()
                    time.sleep(1)  # Wait before next attempt
            except Exception as e:
                self.get_logger().error(f'Error reading from Arduino: {e}')
                self.arduino = None  # Mark as disconnected
            time.sleep(0.01)
    
    def publish_odometry(self):
        """Calculate and publish odometry"""
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        
        if dt > 0:
            # Calculate robot velocities from wheel velocities
            if self.wheel_radius is None:
                self.wheel_radius = 0.033
            if self.wheel_separation is None:
                self.wheel_separation = 0.175
            v_right = self.right_wheel_vel * self.wheel_radius
            v_left = self.left_wheel_vel * self.wheel_radius
            
            # Differential drive kinematics
            linear_vel = (v_right + v_left) / 2.0
            angular_vel = (v_right - v_left) / self.wheel_separation
            
            # Update pose
            delta_x = linear_vel * math.cos(self.theta) * dt
            delta_y = linear_vel * math.sin(self.theta) * dt
            delta_theta = angular_vel * dt
            
            self.x += delta_x
            self.y += delta_y
            self.theta += delta_theta
            
            # Publish odometry
            odom_msg = Odometry()
            odom_msg.header.stamp = current_time.to_msg()
            odom_msg.header.frame_id = 'odom'
            odom_msg.child_frame_id = 'base_link'
            
            # Position
            odom_msg.pose.pose.position.x = self.x
            odom_msg.pose.pose.position.y = self.y
            odom_msg.pose.pose.position.z = 0.0
            
            # Orientation (quaternion from yaw)
            x, y, z, w = quaternion_from_euler(0, 0, self.theta)
            odom_msg.pose.pose.orientation.x = x
            odom_msg.pose.pose.orientation.y = y
            odom_msg.pose.pose.orientation.z = z
            odom_msg.pose.pose.orientation.w = w
            
            # Velocity
            odom_msg.twist.twist.linear.x = linear_vel
            odom_msg.twist.twist.angular.z = angular_vel
            
            self.odom_pub.publish(odom_msg)
            
            # Publish joint states
            joint_msg = JointState()
            joint_msg.header.stamp = current_time.to_msg()
            joint_msg.name = ['base_left_wheel_joint', 'base_right_wheel_joint']
            joint_msg.velocity = [self.left_wheel_vel, self.right_wheel_vel]
            self.joint_pub.publish(joint_msg)
            
            # Publish TF
            self.publish_tf(current_time)
        
        self.last_time = current_time
    
    def publish_tf(self, current_time):
        """Publish odom -> base_footprint transform"""
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        
        x,y,z,w = quaternion_from_euler(0, 0, self.theta)
        odom_msg.pose.pose.orientation.x = x
        odom_msg.pose.pose.orientation.y = y
        odom_msg.pose.pose.orientation.z = z
        odom_msg.pose.pose.orientation.w = w
        
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridge()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
