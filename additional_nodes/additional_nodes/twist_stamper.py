import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class TwistStamper(Node):
    def __init__(self):
        super().__init__('twist_stamper')
        self.sub = self.create_subscription(
            Twist,
            '/bot_controller/cmd_vel_unstamped',
            self.twist_callback,
            10
        )
        self.pub = self.create_publisher(
            TwistStamped,
            '/bot_controller/cmd_vel',
            10
        )

    def twist_callback(self, msg):
        stamped = TwistStamped()
        stamped.header.stamp = self.get_clock().now().to_msg()
        stamped.header.frame_id = 'base_link'  # or any appropriate frame
        stamped.twist = msg
        self.pub.publish(stamped)

def main(args=None):
    rclpy.init(args=args)
    node = TwistStamper()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
