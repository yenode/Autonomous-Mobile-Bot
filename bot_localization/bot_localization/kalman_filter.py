#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu

class KalmanFilter(Node):
    def __init__(self):
        super().__init__("kalman_filter")
        self.odom_sub_ = self.create_subscription(Odometry,"/odom",self.odomCallback,10)
        self.imu_sub_ = self.create_subscription(Imu,"/imu_ekf",self.imuCallback,10)
        self.odom_pub_ = self.create_publisher(Odometry,"/bot_controller/odom_filtered",10)
        
        self.mean_=0.0
        self.variance_=1000.0

        self.motion_variance_=0.5
        self.measurement_variance_=0.5
        
        self.last_angular_z_=0.0
        self.change_in_angular_z_=0.0

        self.is_first_odom_=True
        self.imu_angular_z_=0.0

    def imuCallback(self,msg:Imu):
        self.imu_angular_z_=msg.angular_velocity.z


    def odomCallback(self,msg:Odometry):
        self.kalman_odom_=msg

        if self.is_first_odom_:
            self.is_first_odom_=False
            self.last_angular_z_=msg.twist.twist.angular.z
            self.mean_=msg.twist.twist.angular.z
            return

        self.change_in_angular_z_=msg.twist.twist.angular.z-self.last_angular_z_

        self.prediction_update()
        self.measurement_update()

        self.last_angular_z_=msg.twist.twist.angular.z

        self.kalman_odom_.twist.twist.angular.z=self.mean_

        self.odom_pub_.publish(self.kalman_odom_)
        

    def prediction_update(self):
        self.mean_+=self.change_in_angular_z_
        self.variance_+=self.motion_variance_

    def measurement_update(self):
        self.mean_=(self.variance_*self.imu_angular_z_ + self.measurement_variance_*self.mean_)/(self.variance_+self.measurement_variance_)
        self.variance_=(self.variance_*self.measurement_variance_)/(self.variance_+self.measurement_variance_)


def main():
    rclpy.init()
    kalman_filter=KalmanFilter()
    rclpy.spin(kalman_filter)
    kalman_filter.destroy_node()
    rclpy.shutdown()


if __name__=='__main__':
    main()