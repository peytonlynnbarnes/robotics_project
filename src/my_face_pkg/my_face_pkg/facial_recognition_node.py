#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import face_recognition
import numpy as np

class FacialRecognitionNode(Node):
    def __init__(self):
        super().__init__('facial_recognition_node')
        
        # Bridge to convert ROS images to OpenCV
        self.bridge = CvBridge()
        
        # Subscribe to camera topic
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        # Publish recognized face names
        self.result_pub = self.create_publisher(String, '/face_recognition/results', 10)
        
        # Publish annotated image
        self.annotated_pub = self.create_publisher(Image, '/face_recognition/annotated', 10)
        
        # Known faces database
        self.known_encodings = []
        self.known_names = []
        
        # Load known faces
        self.load_known_faces()
        
        self.get_logger().info('Facial Recognition Node started')

    def load_known_faces(self):
        """Load known face images and encode them."""
        known_faces = {
            'Alice': '/path/to/alice.jpg',
            'Bob': '/path/to/bob.jpg',
        }
        
        for name, path in known_faces.items():
            try:
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    self.get_logger().info(f'Loaded face: {name}')
            except Exception as e:
                self.get_logger().warn(f'Could not load face {name}: {e}')

    def image_callback(self, msg):
        """Process incoming camera frames."""
        try:
            # Convert ROS Image to OpenCV BGR
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'CV bridge error: {e}')
            return
        
        # Resize for faster processing (scale down)
        small = cv2.resize(cv_image, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        
        # Detect face locations and compute encodings
        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)
        
        detected_names = []
        
        for encoding, location in zip(face_encodings, face_locations):
            name = 'Unknown'
            
            if self.known_encodings:
                matches = face_recognition.compare_faces(self.known_encodings, encoding)
                distances = face_recognition.face_distance(self.known_encodings, encoding)
                best_match = np.argmin(distances)
                
                if matches[best_match]:
                    name = self.known_names[best_match]
            
            detected_names.append(name)
            
            # Scale locations back to original size
            top, right, bottom, left = [v * 4 for v in location]
            
            # Draw bounding box and label
            color = (0, 255, 0) if name != 'Unknown' else (0, 0, 255)
            cv2.rectangle(cv_image, (left, top), (right, bottom), color, 2)
            cv2.putText(cv_image, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Publish results
        if detected_names:
            result_msg = String()
            result_msg.data = ', '.join(detected_names)
            self.result_pub.publish(result_msg)
        
        # Publish annotated image
        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(cv_image, 'bgr8')
            annotated_msg.header = msg.header
            self.annotated_pub.publish(annotated_msg)
        except Exception as e:
            self.get_logger().error(f'Publish error: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = FacialRecognitionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()