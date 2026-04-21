import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():

    pkg_sim_bot = get_package_share_directory('sim_bot')

    nav2_params_file = os.path.join(pkg_sim_bot, 'config', 'nav2_params.yaml')
    waypoints_file = os.path.join(pkg_sim_bot, 'config', 'waypoints.yaml')
    rviz_config_file = os.path.join(pkg_sim_bot, 'config', 'nav.rviz')

    map_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_sim_bot, 'maps', 'house_map.yaml'),
        description='Full path to map yaml',
    )
    map_file = LaunchConfiguration('map')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_sim_bot, 'launch', 'sim_gazebo.launch.py')
        )
    )

    # --- Nav2 stack, all brought up by lifecycle_manager ---

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

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[nav2_params_file],
        remappings=[('cmd_vel', '/cmd_vel_nav')],
    )

    # Nav2 publishes geometry_msgs/Twist; Jazzy's diff_drive_controller subscribes
    # to geometry_msgs/TwistStamped. This relay bridges the two with a sim-time stamp.
    cmd_vel_relay = Node(
        package='sim_bot',
        executable='cmd_vel_relay',
        name='cmd_vel_relay',
        output='screen',
        parameters=[{'use_sim_time': True}],
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

    # --- Application nodes ---

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    waypoint_navigator = Node(
        package='sim_bot',
        executable='waypoint_navigator',
        name='waypoint_navigator',
        output='screen',
        parameters=[waypoints_file, {'use_sim_time': True}],
    )

    return LaunchDescription([
        map_arg,
        sim,
        map_server,
        amcl,
        planner_server,
        controller_server,
        behavior_server,
        bt_navigator,
        lifecycle_manager,
        rviz,
        waypoint_navigator,
        cmd_vel_relay,
    ])
