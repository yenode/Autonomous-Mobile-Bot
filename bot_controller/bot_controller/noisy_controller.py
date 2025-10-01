#!/usr/bin/env python3
import  rclpy
from rclpy.node import Node
from rclpy.time import Time 
from sensor_msgs.msg import JointState
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import numpy as np
from tf2_ros import TransformBroadcaster
import math
from tf_transformations import quaternion_from_euler

class NoisyController(Node):
    def __init__(self):
        super().__init__("noisy_controller")
        self.wheel_radius=0.108
        self.wheel_separation=0.76322

        self.prev_pos_right_=0.0
        self.prev_pos_left_=0.0
        self.prev_time_=self.get_clock().now().nanoseconds*10e-10
        self.x_=0.0
        self.y_=0.0
        self.theta_=0.0

        self.joint_sub_ = self.create_subscription(JointState,"/joint_states",self.jointCallback,10)
        self.odom_pub_ = self.create_publisher(Odometry,"/bot_controller/odom_noisy",10)
        

        self.odom_msg_=Odometry()
        self.odom_msg_.header.frame_id="odom"
        self.odom_msg_.child_frame_id="base_footprint"
        self.odom_msg_.pose.pose.position.x=0.0
        self.odom_msg_.pose.pose.position.y=0.0
        self.odom_msg_.pose.pose.position.z=0.0
        self.odom_msg_.pose.pose.orientation.x=0.0
        self.odom_msg_.pose.pose.orientation.y=0.0
        self.odom_msg_.pose.pose.orientation.z=0.0
        self.odom_msg_.pose.pose.orientation.w=1.0

        self.br_=TransformBroadcaster(self)
        self.tf_stamped_=TransformStamped()
        self.tf_stamped_.header.frame_id="odom"
        self.tf_stamped_.child_frame_id="base_footprint"

        self.timer_=self.create_timer(0.1,self.timerCallback)
        


    def jointCallback(self,msg:JointState):
        wheel_encoder_left_=msg.position[0]
        wheel_encoder_right_=msg.position[1]

        left_wheel_now_=wheel_encoder_left_-self.prev_pos_left_
        right_wheel_now_=wheel_encoder_right_-self.prev_pos_right_

        self.prev_pos_left_=msg.position[0]
        self.prev_pos_right_=msg.position[1]

        time_elapsed_=msg.header.stamp.nanosec*10e-10 - self.prev_time_

        self.prev_time_=msg.header.stamp.nanosec*10e-10

        ang_vel_left = left_wheel_now_/time_elapsed_
        ang_vel_right = right_wheel_now_/time_elapsed_

        lin_vel_left=ang_vel_left*self.wheel_radius
        lin_vel_right=ang_vel_right*self.wheel_radius

        lin_vel_robot = (lin_vel_right + lin_vel_left)/2
        ang_vel_robot = (lin_vel_right-lin_vel_left)/self.wheel_separation

        theta_update= ang_vel_robot*time_elapsed_
        self.theta_+=theta_update

        self.x_+=lin_vel_robot*math.cos(self.theta_)*time_elapsed_
        self.y_+=lin_vel_robot*math.sin(self.theta_)*time_elapsed_

        q=quaternion_from_euler(0,0,self.theta_)
        self.odom_msg_.pose.pose.position.x=self.x_
        self.odom_msg_.pose.pose.position.y=self.y_
        self.odom_msg_.pose.pose.position.z=0.0
        self.odom_msg_.pose.pose.orientation.x=q[0]
        self.odom_msg_.pose.pose.orientation.y=q[1]
        self.odom_msg_.pose.pose.orientation.z=q[2]
        self.odom_msg_.pose.pose.orientation.w=q[3]
        self.odom_msg_.twist.twist.linear.x=lin_vel_robot
        self.odom_msg_.twist.twist.angular.z=ang_vel_robot
        self.odom_pub_.publish(self.odom_msg_)

        

    def timerCallback(self):
        q=quaternion_from_euler(0,0,self.theta_)
        self.tf_stamped_.transform.translation.x = self.x_
        self.tf_stamped_.transform.translation.y = self.y_
        self.tf_stamped_.transform.translation.z = 0.0
        self.tf_stamped_.transform.rotation.x = q[0]
        self.tf_stamped_.transform.rotation.y = q[1]
        self.tf_stamped_.transform.rotation.z = q[2]
        self.tf_stamped_.transform.rotation.w = q[3]
        self.tf_stamped_.header.stamp = self.get_clock().now().to_msg()
        self.br_.sendTransform(self.tf_stamped_)


def main():
    rclpy.init()
    noisy_controller=NoisyController()
    rclpy.spin(noisy_controller)
    noisy_controller.destroy_node()
    rclpy.shutdown()


if __name__=='__main__':
    main()