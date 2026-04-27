from launch import LaunchDescription

from launch_ros.actions import Node


def generate_launch_description():

    # teleop_twist_keyboard in its own xterm so it has a TTY for keystrokes.
    # Unstamped Twist — matches both diff_drive_controller (use_stamped_vel: false)
    # and Nav2's controller_server output.
    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        prefix='xterm -e',
        output='screen',
        parameters=[{'stamped': False}],
        remappings=[('/cmd_vel', '/diff_drive_controller/cmd_vel')],
    )

    return LaunchDescription([
        teleop,
    ])
