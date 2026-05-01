import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from .facial_recognition import DeliveryVision
from voice_pkg.audio_feedback import speak

class FaceNode(Node):
    def __init__(self):
        super().__init__('face_node')
        self.target_person = None
        self.create_subscription(String, '/target_person', self.set_target, 10)
        self.create_subscription(String, '/nav_status', self.nav_status_callback, 10)
        self.verified_pub = self.create_publisher(String, '/person_verified', 10)

    def set_target(self, msg):
        self.target_person = msg.data

    def nav_status_callback(self, msg):
        if msg.data == "moving" and self.target_person:
            self.get_logger().info("Navigation moving. Starting face recognition...")
            vision = DeliveryVision(self.target_person, speak)
            if vision.run():
                self.verified_pub.publish(String(data="verified"))
                self.get_logger().info("{self.target_person} verified!")

def main(args=None):
    rclpy.init(args=args)
    node = FaceNode()
    rclpy.spin(node)
    rclpy.shutdown()
