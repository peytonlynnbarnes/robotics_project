# Lowlevel Hardware Control Package

This ROS2 package provides low-level hardware control for robot motors and IMU sensors.

## Package Contents

- **servo_node**: Controls servo motors using GPIO pin 25
- **stepper_left_node**: Controls left stepper motor (motor 1)
- **stepper_right_node**: Controls right stepper motor (motor 2)  
- **imu_node**: Publishes IMU data from MPU6050 sensor

## Building

```bash
cd ~/robotics_project
colcon build --packages-select lowlevel
```

## Running

### Launch all nodes at once:
```bash
source install/setup.bash
ros2 launch lowlevel lowlevel.launch.py
```

### Run individual nodes:
```bash
ros2 run lowlevel servo_node
ros2 run lowlevel stepper_left_node
ros2 run lowlevel stepper_right_node
ros2 run lowlevel imu_node
```

## Node Details

### servo_node
- **Node Name**: servo_node
- **GPIO Pin**: 25 (BCM)
- **Functionality**: Controls servo motor with PWM signals

### stepper_left_node
- **Node Name**: stepper_left_node
- **GPIO Pins**: 
  - DIR: 6 (BCM 6)
  - STEP: 5 (BCM 5)
- **Subscribers**: 
  - `/cmd_vel` (geometry_msgs/Twist)
- **Publishers**: 
  - `/stepperLeft` (std_msgs/Int32)

### stepper_right_node
- **Node Name**: stepper_right_node
- **GPIO Pins**: 
  - DIR: 24 (BCM 24)
  - STEP: 23 (BCM 23)
- **Subscribers**: 
  - `/cmd_vel` (geometry_msgs/Twist)
- **Publishers**: 
  - `/stepperRight` (std_msgs/Int32)

### imu_node
- **Node Name**: imu_node
- **I2C Address**: 0x68 (MPU6050)
- **Publishers**: 
  - `/imu/data` (sensor_msgs/Imu)
- **Frequency**: 50 Hz

## Dependencies

- rclpy
- gpiozero
- smbus2
- std_msgs
- geometry_msgs
- sensor_msgs

## Notes

- This package requires GPIO access on a Raspberry Pi
- IMU sensor requires I2C bus (typically /dev/i2c-1 on RPi)
- The servo, stepper motor 1, and stepper motor 2 nodes should be run with appropriate GPIO permissions
