"""Real-robot Nav2 + waypoint navigator.

Nav2's controller_server publishes geometry_msgs/Twist on /cmd_vel — which is
exactly what the real robot eats. No cmd_vel_relay needed (that existed in sim
only because Jazzy's diff_drive_controller wants TwistStamped).

Requires a saved map. Map first with real_slam, save with:
  ros2 run nav2_map_server map_saver_cli -f src/real_bot/maps/<name>
then launch with map:=<path>.
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

    nav2_params_file = os.path.join(pkg_real_bot, 'config', 'nav2_params.yaml')
    waypoints_file = os.path.join(pkg_real_bot, 'config', 'waypoints.yaml')
    rviz_config_file = os.path.join(pkg_real_bot, 'config', 'nav.rviz')

    map_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_real_bot, 'maps', 'map.yaml'),
        description='Full path to map yaml',
    )
    map_file = LaunchConfiguration('map')

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_real_bot, 'launch', 'real_bringup.launch.py')
        )
    )

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[nav2_params_file, {'yaml_filename': map_file}],
    )

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[nav2_params_file],
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[nav2_params_file],
    )

    # No remap: real robot listens to /cmd_vel directly.
    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav2_params_file],
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[nav2_params_file],
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[nav2_params_file],
    )

    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager',
        output='screen',
        parameters=[nav2_params_file],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': False}],
        output='screen',
    )

    waypoint_navigator = Node(
        package='real_bot',
        executable='waypoint_navigator',
        name='waypoint_navigator',
        output='screen',
        parameters=[waypoints_file, {'use_sim_time': False}],
    )

    return LaunchDescription([
        map_arg,
        bringup,
        map_server,
        amcl,
        planner_server,
        controller_server,
        behavior_server,
        bt_navigator,
        lifecycle_manager,
        rviz,
        waypoint_navigator,
    ])
