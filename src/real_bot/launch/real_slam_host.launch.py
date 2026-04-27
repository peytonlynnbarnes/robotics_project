"""Host-side SLAM: slam_toolbox + RViz only.

Companion to real_bringup_dr.launch.py running on the Pi. The Pi publishes
/scan, /tf, /tf_static, /odom; this launch consumes them over the network
and produces /map + map -> odom TF.

Make sure ROS_DOMAIN_ID matches the Pi and discovery is reachable.
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import EmitEvent, RegisterEventHandler

from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState

from lifecycle_msgs.msg import Transition


def generate_launch_description():

    pkg_real_bot = get_package_share_directory('real_bot')

    slam_params_file = os.path.join(pkg_real_bot, 'config', 'slam_params.yaml')
    rviz_config_file = os.path.join(pkg_real_bot, 'config', 'slam.rviz')

    slam = LifecycleNode(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': False},
        ],
    )

    emit_configure = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=lambda node: node == slam,
            transition_id=Transition.TRANSITION_CONFIGURE,
        )
    )

    emit_activate = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=slam,
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=lambda node: node == slam,
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    )
                )
            ],
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
        slam,
        emit_configure,
        emit_activate,
        rviz,
    ])
