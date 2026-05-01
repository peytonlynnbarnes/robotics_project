from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='my_voice_pkg', executable='voice_node', name='voice_node'),
        Node(package='my_face_pkg', executable='face_node', name='face_node'),
        Node(package='real_bot', executable='controller_node', name='controller_node'),
        Node(package='navigation_pkg', executable='nav_node', name='nav_node'),
    ])
