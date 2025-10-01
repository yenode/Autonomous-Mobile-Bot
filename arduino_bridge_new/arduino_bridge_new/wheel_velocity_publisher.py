#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import TwistStamped
import math

class WheelVelocityPublisher(Node):
    def __init__(self):
        super().__init__('wheel_velocity_publisher')
        
        # Parameters
        self.declare_parameter('wheel_radius', 0.033)  # meters
        self.declare_parameter('wheel_separation', 0.175)  # meters
        
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        
        # Publishers
        self.wheel_vel_pub = self.create_publisher(Float64MultiArray, 'wheel_velocities', 10)
        
        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            TwistStamped, '/bot_controller/cmd_vel', self.cmd_vel_callback, 10)
        
        self.get_logger().info('Wheel Velocity Publisher Node Started')
        self.get_logger().info(f'Wheel radius: {self.wheel_radius}m, Wheel separation: {self.wheel_separation}m')
    
    def cmd_vel_callback(self, msg:TwistStamped):
        """Convert twist message to wheel velocities and publish"""
        # Differential drive kinematics
        # v_right = (linear_vel + angular_vel * wheel_separation / 2) / wheel_radius
        # v_left = (linear_vel - angular_vel * wheel_separation / 2) / wheel_radius
        
        linear_vel = msg.twist.linear.x  # m/s
        angular_vel = msg.twist.angular.z  # rad/s
        
        # Calculate wheel velocities in rad/s
        right_wheel_vel = (linear_vel + (angular_vel * self.wheel_separation / 2.0)) / self.wheel_radius
        left_wheel_vel = (linear_vel - (angular_vel * self.wheel_separation / 2.0)) / self.wheel_radius
        
        # Create and publish wheel velocity message
        wheel_vel_msg = Float64MultiArray()
        wheel_vel_msg.data = [right_wheel_vel, left_wheel_vel]
        
        self.wheel_vel_pub.publish(wheel_vel_msg)
        
        # Log for debugging
        self.get_logger().debug(f'Twist: linear={linear_vel:.3f}, angular={angular_vel:.3f}')
        self.get_logger().debug(f'Wheel velocities: right={right_wheel_vel:.3f}, left={left_wheel_vel:.3f} rad/s')

def main(args=None):
    rclpy.init(args=args)
    node = WheelVelocityPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
