import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_node')
        self.target_person = None
        self.target_location = None

        self.create_subscription(String, '/target_person', self.person_cb, 10)
        self.create_subscription(String, '/target_location', self.location_cb, 10)
        self.nav_pub = self.create_publisher(String, '/nav_goal', 10)

    def person_cb(self, msg):
        self.target_person = msg.data
        self.check_ready()

    def location_cb(self, msg):
        self.target_location = msg.data
        self.check_ready()

    def check_ready(self):
        if self.target_person and self.target_location:
            nav_msg = String(data=self.target_location)
            self.nav_pub.publish(nav_msg)
            self.get_logger().info(f"Nav goal sent: {self.target_location}")

def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()
