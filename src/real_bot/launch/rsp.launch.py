import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

import xacro


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')

    pkg_path = get_package_share_directory('real_bot')
    xacro_file = os.path.join(pkg_path, 'description', 'robot.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock (real robot defaults to false)',
    )

    params = {
        'robot_description': robot_description_config.toxml(),
        'use_sim_time': use_sim_time,
    }
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params],
    )

    return LaunchDescription([
        declare_use_sim_time,
        node_robot_state_publisher,
    ])
