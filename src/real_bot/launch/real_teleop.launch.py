"""Real-robot keyboard teleop.

Publishes unstamped Twist on /cmd_vel — the real robot subscribes to /cmd_vel
directly. No remap, no TwistStamped (unlike sim, which goes through diff_drive_controller).
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    pkg_real_bot = get_package_share_directory('real_bot')

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_real_bot, 'launch', 'real_bringup.launch.py')
        )
    )

    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        prefix='xterm -e',
        output='screen',
        parameters=[{'stamped': False}],
    )

    return LaunchDescription([
        bringup,
        teleop,
    ])
