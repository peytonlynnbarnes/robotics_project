"""Minimal SLAM launch — equivalent to running these two by hand:

  ros2 run slam_toolbox async_slam_toolbox_node \\
    --ros-args --params-file <slam_params.yaml> -p use_sim_time:=false

  ros2 lifecycle set /slam_toolbox configure
  ros2 lifecycle set /slam_toolbox activate

No bringup, no RViz, no event-handler dance. The lifecycle transitions are
issued via a shell loop that retries until the service is reachable, which
is robust against the Jazzy race where EmitEvent fires too early.
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    pkg_real_bot = get_package_share_directory('real_bot')
    slam_params_file = os.path.join(pkg_real_bot, 'config', 'slam_params.yaml')

    slam_toolbox = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[slam_params_file, {'use_sim_time': False}],
        output='screen',
    )

    activate = TimerAction(
        period=2.0,
        actions=[
            ExecuteProcess(
                cmd=['bash', '-c',
                     'for i in 1 2 3 4 5 6 7 8 9 10; do '
                     '  ros2 lifecycle set /slam_toolbox configure >/dev/null 2>&1 && break; '
                     '  sleep 1; '
                     'done; '
                     'sleep 1; '
                     'for i in 1 2 3 4 5 6 7 8 9 10; do '
                     '  ros2 lifecycle set /slam_toolbox activate >/dev/null 2>&1 && break; '
                     '  sleep 1; '
                     'done; '
                     'echo "[slam_simple] state: $(ros2 lifecycle get /slam_toolbox 2>&1)"'],
                output='screen',
            )
        ],
    )

    return LaunchDescription([
        slam_toolbox,
        activate,
    ])
