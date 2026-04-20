import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():

    pkg_sim_bot = get_package_share_directory('sim_bot')

    # Bring up Gazebo + robot + controllers + lidar bridge
    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_sim_bot, 'launch', 'sim_gazebo.launch.py')
        )
    )

    # teleop_twist_keyboard in its own xterm so it has a TTY for keystrokes.
    # `stamped: True` makes it publish geometry_msgs/TwistStamped, which is
    # what this project's diff_drive_controller subscribes to.
    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        prefix='xterm -e',
        output='screen',
        parameters=[{'stamped': True}],
        remappings=[('/cmd_vel', '/diff_drive_controller/cmd_vel')],
    )

    return LaunchDescription([
        sim,
        teleop,
    ])
