"""Real-robot dead-reckoning bringup + RViz.

slam_toolbox has been removed — run it on the host with
  ros2 launch real_bot real_slam_simple.launch.py
which talks to this Pi-side bringup over the network.

odom -> base_link comes from stepper_odom; map -> odom comes from
slam_toolbox running on the host.
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():

    pkg_real_bot = get_package_share_directory('real_bot')

    rviz_config_file = os.path.join(pkg_real_bot, 'config', 'slam.rviz')

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_real_bot, 'launch', 'real_bringup_dr.launch.py')
        )
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': False}],
        output='screen',
    )

    return LaunchDescription([
        bringup,
        rviz,
    ])
