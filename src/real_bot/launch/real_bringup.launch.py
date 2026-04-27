"""Real-robot bringup: TF + sensors + EKF.

Assumes the robot's onboard firmware/driver:
  - subscribes to /cmd_vel (geometry_msgs/Twist) and drives the motors
  - publishes /odom (nav_msgs/Odometry) from wheel encoders
  - publishes /imu/data (sensor_msgs/Imu) at >= 30 Hz with gyro + accel

This launch starts robot_state_publisher (TF from URDF), joint_state_publisher
(default zero positions for the wheel joints — needed only for RViz to render
the wheels), the Hokuyo lidar driver on /scan, and robot_localization's EKF
fusing /odom (vx) + /imu/data (vyaw) into /odometry/filtered + odom->base_link TF.

If your /odom publisher also broadcasts the odom->base_link TF, disable that on
its end so EKF is the only TF publisher (otherwise the two will fight).
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

    # Default zero positions for the four wheel continuous joints so RViz can
    # render the robot. Nav/SLAM don't depend on wheel angles.
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
        output='screen'
    )

    # Hokuyo driver. Older non-lifecycle urg_node binary.
    # For USB Hokuyos (URG-04LX-UG01, etc.) use serial_port. For ethernet Hokuyos
    # (UST-10LX, UST-20LX) set lidar_ip_address:=192.168.0.10 (or your bot's IP).
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

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(pkg_real_bot, 'config', 'ekf.yaml'),
            {'tf_buffer_duration': 30.0},
        ],
    )

    return LaunchDescription([
        declare_lidar_port,
        rsp_launch,
        joint_state_publisher,
        stepper_odom,
        urg_node,
        ekf_node,
    ])
