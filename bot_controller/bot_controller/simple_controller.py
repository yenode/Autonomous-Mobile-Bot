#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Float64MultiArray
import numpy as np

class SimpleController(Node):
    def __init__(self):
        super().__init__("simple_controller")
        self.wheel_radius=0.108
        self.wheel_separation=0.38161

        self.vel_sub_=self.create_subscription(TwistStamped,"/bot_controller/cmd_vel",self.velCallback,10)
        self.cmd_pub_=self.create_publisher(Float64MultiArray,"/simple_controller/commands",10)


    def velCallback(self,msg:TwistStamped):
        cmd=Float64MultiArray()
        self.get_logger().info("Angular velocity %f" % msg.twist.angular.z)
        cmd.data=np.array([msg.twist.linear.x/2 + msg.twist.angular.z*0.140805,
                        msg.twist.linear.x/2 - msg.twist.angular.z*0.140805])
        # cmd.data=np.array([5.0,5.0,5.0,5.0])

        self.cmd_pub_.publish(cmd)

def main():
    rclpy.init()

    simple_controller = SimpleController()
    rclpy.spin(simple_controller)
    
    simple_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()