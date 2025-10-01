#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus
import math

# MPU-6050 Register Addresses
PWR_MGMT_1   = 0x6B
ACCEL_CONFIG = 0x1C
GYRO_CONFIG  = 0x1B
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47
DEVICE_ADDRESS = 0x68

# Physical and Scaling Constants
# From datasheet: Sensitivity Scale Factor for Accelerometer at ±2g range
ACCEL_SCALE_MODIFIER = 16384.0
# From datasheet: Sensitivity Scale Factor for Gyroscope at ±2000 °/s range
GYRO_SCALE_MODIFIER = 16.4
GRAVITY_MS2 = 9.80665


class IMU_Publisher(Node):
    """
    A ROS 2 node to publish IMU data from an MPU-6050 sensor using smbus.
    """
    def __init__(self):
        super().__init__("imu_publisher")
        
        # ROS 2 Publisher Setup
        self.imu_publisher_ = self.create_publisher(Imu, "/imu_out", 10)
        self.imu_msg_ = Imu()
        self.imu_msg_.header.frame_id = "imu_link"

        # Set covariance to -1 to indicate the data is not available
        self.imu_msg_.orientation_covariance[0] = -1.0
        self.imu_msg_.angular_velocity_covariance[0] = -1.0
        self.imu_msg_.linear_acceleration_covariance[0] = -1.0
        
        # Timer Setup
        timer_period = 0.1  # seconds (for 50 Hz frequency)
        self.timer_ = self.create_timer(timer_period, self.timer_callback)

        # I2C and Sensor Initialization
        self.bus_ = None
        self.init_i2c()

    def init_i2c(self):
        """Initializes the I2C bus and configures the MPU-6050."""
        try:
            self.bus_ = smbus.SMBus(1)  # Use I2C bus 1 for Raspberry Pi
            # Wake up the MPU-6050 (clears the sleep bit)
            self.bus_.write_byte_data(DEVICE_ADDRESS, PWR_MGMT_1, 0x00)
            # Set Accelerometer Full Scale Range to ±2g
            self.bus_.write_byte_data(DEVICE_ADDRESS, ACCEL_CONFIG, 0x00)
            # Set Gyroscope Full Scale Range to ±2000 °/s
            self.bus_.write_byte_data(DEVICE_ADDRESS, GYRO_CONFIG, 0x18)
            self.get_logger().info("MPU-6050 successfully initialized.")
        except OSError as e:
            self.get_logger().error(f"Failed to initialize MPU-6050: {e}")
            self.bus_ = None

    def read_raw_data(self, addr):
        """Reads two bytes from the specified address and combines them."""
        high = self.bus_.read_byte_data(DEVICE_ADDRESS, addr)
        low = self.bus_.read_byte_data(DEVICE_ADDRESS, addr + 1)
        
        # Combine high and low bytes
        value = (high << 8) | low
        
        # Convert to signed 16-bit integer
        if value > 32768:
            value -= 65536
        return value

    def timer_callback(self):
        """Periodically reads sensor data and publishes it."""
        if self.bus_ is None:
            self.get_logger().warn("I2C bus not available. Retrying initialization...")
            self.init_i2c()
            return

        try:
            # Read raw accelerometer and gyroscope values
            accel_x_raw = self.read_raw_data(ACCEL_XOUT_H)
            accel_y_raw = self.read_raw_data(ACCEL_YOUT_H)
            accel_z_raw = self.read_raw_data(ACCEL_ZOUT_H)
            
            gyro_x_raw = self.read_raw_data(GYRO_XOUT_H)
            gyro_y_raw = self.read_raw_data(GYRO_YOUT_H)
            gyro_z_raw = self.read_raw_data(GYRO_ZOUT_H)

            # --- Populate IMU Message with Correctly Scaled Data ---

            # Header
            self.imu_msg_.header.stamp = self.get_clock().now().to_msg()
            
            # Linear Acceleration (in m/s^2)
            self.imu_msg_.linear_acceleration.x = (accel_x_raw / ACCEL_SCALE_MODIFIER) * GRAVITY_MS2
            self.imu_msg_.linear_acceleration.y = (accel_y_raw / ACCEL_SCALE_MODIFIER) * GRAVITY_MS2
            self.imu_msg_.linear_acceleration.z = (accel_z_raw / ACCEL_SCALE_MODIFIER) * GRAVITY_MS2
            
            # Angular Velocity (in rad/s)
            self.imu_msg_.angular_velocity.x = (gyro_x_raw / GYRO_SCALE_MODIFIER) * (math.pi / 180.0)
            self.imu_msg_.angular_velocity.y = (gyro_y_raw / GYRO_SCALE_MODIFIER) * (math.pi / 180.0)
            self.imu_msg_.angular_velocity.z = (gyro_z_raw / GYRO_SCALE_MODIFIER) * (math.pi / 180.0)
            
            # Orientation is not provided by MPU-6050
            self.imu_msg_.orientation.x = 0.0
            self.imu_msg_.orientation.y = 0.0
            self.imu_msg_.orientation.z = 0.0
            self.imu_msg_.orientation.w = 1.0 # Neutral orientation

            # Publish the message
            self.imu_publisher_.publish(self.imu_msg_)

        except OSError as e:
            self.get_logger().error(f"I2C communication error: {e}")
            self.bus_ = None # Flag bus as unavailable to trigger re-initialization


def main(args=None):
    rclpy.init(args=args)
    imu_publisher = IMU_Publisher()
    
    try:
        rclpy.spin(imu_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        imu_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()