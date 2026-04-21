import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

from launch_ros.actions import Node


def generate_launch_description():

    # Get package paths
    pkg_sim_bot = get_package_share_directory('sim_bot')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Include robot_state_publisher launch
    rsp_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_sim_bot, 'launch', 'rsp.launch.py')
        ),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    # World file selection (default: house.world)
    declare_world = DeclareLaunchArgument(
        'world', default_value='house.world',
        description='World file name in sim_bot/worlds/',
    )
    world_file = PathJoinSubstitution([
        FindPackageShare('sim_bot'), 'worlds', LaunchConfiguration('world')
    ])

    # Start Gazebo (world must include Sensors system plugin for gpu_lidar)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r ', world_file]
        }.items()
    )

    # Spawn robot into Gazebo from /robot_description
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'sim_bot',
            '-z', '0.2'
        ],
        output='screen'
    )

    # Spawn joint state broadcaster
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    # Spawn diff drive controller
    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--controller-manager', '/controller_manager',
            '--ros-args',
            '-p', 'use_sim_time:=true'
        ],
        output='screen'
    )
    

    # Start joint_state_broadcaster after robot spawn finishes
    delay_joint_state_broadcaster_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )

    # Start diff_drive_controller after joint_state_broadcaster is spawned
    delay_diff_drive_controller_after_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[diff_drive_controller_spawner],
        )
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # Bridge the lidar /scan topic from Gazebo to ROS2 (one-way: gz -> ros)
    lidar_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'],
        output='screen'
    )

    # Bridge the IMU topic from Gazebo to ROS2 (one-way: gz -> ros)
    imu_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/imu@sensor_msgs/msg/Imu[gz.msgs.IMU'],
        output='screen'
    )

    # EKF fuses wheel odometry + IMU and publishes the odom -> base_link TF.
    # diff_drive_controller has enable_odom_tf: false so this is the only publisher.
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(pkg_sim_bot, 'config', 'ekf.yaml')],
    )

    return LaunchDescription([
        declare_world,
        gazebo,
        clock_bridge,
        lidar_bridge,
        imu_bridge,
        rsp_launch,
        spawn_entity,
        delay_joint_state_broadcaster_after_spawn,
        delay_diff_drive_controller_after_jsb,
        ekf_node,
    ])