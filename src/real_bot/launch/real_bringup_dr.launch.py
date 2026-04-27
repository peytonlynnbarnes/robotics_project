"""Real-robot bringup, dead-reckoning variant.

No EKF, no IMU fusion. stepper_odom integrates wheel ticks and broadcasts
the odom -> base_link TF directly. Pose drifts purely from wheel slip /
calibration error — SLAM is what corrects it via map -> odom.

Brings up: robot_state_publisher, joint_state_publisher (RViz only),
stepper_odom (with publish_tf:=true), urg_node.
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_real_bot = get_package_share_directory('real_bot')

    declare_lidar_port = DeclareLaunchArgument(
        'lidar_serial_port',
        default_value='/dev/ttyACM0',
        description='Serial device for USB Hokuyo. Ignored if lidar_ip_address is set.',
    )

    rsp_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_real_bot, 'launch', 'rsp.launch.py')
        ),
        launch_arguments={'use_sim_time': 'false'}.items(),
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': False}],
    )

    stepper_odom = Node(
        package='real_bot',
        executable='stepper_odom',
        name='stepper_odom',
        output='screen',
        parameters=[{'publish_tf': True}],
    )

    urg_node = Node(
        package='urg_node',
        executable='urg_node_driver',
        name='urg_node',
        output='screen',
        parameters=[{
            'serial_port': LaunchConfiguration('lidar_serial_port'),
            'laser_frame_id': 'laser_frame',
            'angle_min': -1.5708,
            'angle_max':  1.5708,
            'laser_max_range': 5.5,
        }],
    )

    return LaunchDescription([
        declare_lidar_port,
        rsp_launch,
        joint_state_publisher,
        stepper_odom,
        urg_node,
    ])
