import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from .voice_command import listen_for_command
from .audio_feedback import speak

class VoiceNode(Node):
    def __init__(self):
        super().__init__('voice_node')
        self.person_pub = self.create_publisher(String, '/target_person', 10)
        self.location_pub = self.create_publisher(String, '/target_location', 10)
        self.run_pipeline()

    def run_pipeline(self):
        speak("Robot active.")
        while rclpy.ok():
            speak("Who should I deliver to?")
            person = listen_for_command()
            if not person:
                speak("Please try again.")
                continue

            speak(f"Where should I deliver?")
            location = listen_for_command()
            if not location:
                speak("Please try again.")
                continue

            self.publish_data(person, location)
            speak(f"Targets set.")
            break 

    def publish_data(self, person, location):
        self.person_pub.publish(String(data=person))
        self.location_pub.publish(String(data=location))

def main(args=None):
    rclpy.init(args=args)
    node = VoiceNode()
    rclpy.spin(node)
    rclpy.shutdown()
