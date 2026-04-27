from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Launch all lowlevel hardware control nodes."""
    
    # Servo node
    servo_node = Node(
        package='lowlevel',
        executable='servo_node',
        name='servo_node',
        output='screen',
    )

    # Left stepper motor node
    stepper_left_node = Node(
        package='lowlevel',
        executable='stepper_left_node',
        name='stepper_left_node',
        output='screen',
    )

    # Right stepper motor node
    stepper_right_node = Node(
        package='lowlevel',
        executable='stepper_right_node',
        name='stepper_right_node',
        output='screen',
    )

    # IMU node
    imu_node = Node(
        package='lowlevel',
        executable='imu_node',
        name='imu_node',
        output='screen',
    )

    return LaunchDescription([
        servo_node,
        stepper_left_node,
        stepper_right_node,
        imu_node,
    ])
