# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS2 differential drive robot simulation ("sim_bot") using Gazebo. Four-wheeled robot with paired left/right differential drive control via ros2_control. Equipped with a 360° 2D lidar feeding `slam_toolbox` for online SLAM.

**Stack**: ROS 2 Jazzy + Gazebo Harmonic (gz-sim 8) on Ubuntu 24.04. Plugin/sensor types must use the `gz` (not `ignition`) namespace.

## Prerequisites

```bash
sudo apt install ros-jazzy-slam-toolbox xterm
```
- `slam_toolbox` is required by `sim_slam.launch.py`.
- `xterm` is required by `sim_teleop.launch.py` (teleop_twist_keyboard needs a TTY for keystrokes).

## Build & Run Commands

```bash
# Build
colcon build --symlink-install

# Source workspace (required after build and in each new terminal)
source install/setup.bash

# Sim only
ros2 launch sim_bot sim_gazebo.launch.py

# Sim + keyboard teleop (xterm window pops up; focus it and use i/j/k/l)
ros2 launch sim_bot sim_teleop.launch.py

# Sim + slam_toolbox + RViz (drive with teleop in another terminal to map)
ros2 launch sim_bot sim_slam.launch.py

# Save the map after mapping
ros2 run nav2_map_server map_saver_cli -f ~/sim_bot_map

# Manual cmd_vel (TwistStamped — diff_drive_controller expects stamped)
ros2 topic pub /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  "{header: {frame_id: '', stamp: {sec: 0, nanosec: 0}}, twist: {linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.3}}}" -r 10

# Kill all simulation processes
pkill -f gz; pkill -f slam_toolbox; pkill -f rviz2; pkill -f ros2_control_node; pkill -f controller_manager; pkill -f robot_state_publisher; pkill -f spawner
```

## Architecture

### Package: sim_bot (`src/sim_bot/`)

Build system: ament_cmake via colcon. No custom C++/Python nodes — the package is entirely launch files, xacro descriptions, and config.

**Robot description** (`description/`): Xacro files composing the URDF.
- `robot.urdf.xacro` — top-level, includes all others and instantiates each macro
- `robot_core.xacro` — chassis (0.3×0.3×0.25m) and 4 wheel joints
- `ros2_control.xacro` — hardware interface definitions (velocity command, position/velocity state per wheel)
- `gazebo_control_plugin.xacro` — gz_ros2_control plugin bridge
- `lidar.xacro` — `laser_frame` link mounted on top of chassis + `gpu_lidar` Gazebo sensor
- `inertial_macros.xacro` — reusable inertia calculators (sphere, box, cylinder)

**Control pipeline**: Gazebo physics → `gz_ros2_control/GazeboSimSystem` → controller_manager (100 Hz) → `diff_drive_controller` + `joint_state_broadcaster`.

**Launch sequence** (`launch/sim_gazebo.launch.py`): Gazebo → clock bridge → lidar bridge → robot_state_publisher → spawn entity → joint_state_broadcaster → diff_drive_controller. Each controller spawns after the previous via event handlers.

**Composite launches**:
- `sim_teleop.launch.py` — `sim_gazebo` + `teleop_twist_keyboard` (xterm prefix, `stamped:=true`, remapped to `/diff_drive_controller/cmd_vel`)
- `sim_slam.launch.py` — `sim_gazebo` + `async_slam_toolbox_node` + `rviz2` (loads `config/slam.rviz`)

**Controller config** (`config/controllers.yaml`): Diff drive with wheel_separation=0.30m, wheel_radius=0.05m, publish_rate=50Hz. Left wheels: `[left_front_wheel_joint, left_rear_wheel_joint]`, right wheels: `[right_front_wheel_joint, right_rear_wheel_joint]`. **`base_frame_id: base_link`** — the standard ROS convention. Anything that needs the robot base frame (slam_toolbox, nav2) must use `base_link`.

### Sensors

**Lidar** (`description/lidar.xacro`): 360° 2D lidar mounted on top of chassis at `xyz="0 0 0.27"` (≈0.32 m above ground). 360 samples, 0.12–12 m range, 10 Hz, gaussian noise σ=0.01. Defined as `gpu_lidar` sensor with `<gz_frame_id>laser_frame</gz_frame_id>` so the published `LaserScan.header.frame_id` matches the URDF link. Bridged Gazebo→ROS by `lidar_bridge` in `sim_gazebo.launch.py` as `/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan`.

### SLAM

`slam_toolbox` async online mode, configured in `config/slam_params.yaml`. The `diff_drive_controller` already provides `odom → chassis`; slam_toolbox produces `map → odom`. **`base_frame: base_link`** in `slam_params.yaml` must match the controller's `base_frame_id` or TF resolution will fail.

### Package: face_recognition (`src/face_recognition/`)

Placeholder — currently empty.

## Key ROS2 Topics

- `/diff_drive_controller/cmd_vel` (TwistStamped) — velocity input
- `/diff_drive_controller/odom` — odometry output
- `/joint_states` — wheel positions/velocities
- `/scan` (LaserScan) — lidar output, frame_id `laser_frame`
- `/map` (OccupancyGrid) — slam_toolbox output (only when sim_slam launched)
- `/tf`, `/tf_static` — transform tree (`map → odom → chassis → wheels`, `chassis → laser_frame`)

## Wheel Geometry

Left wheels rotate along Z=+1, right wheels along Z=-1. Wheel radius=0.08255m, width=0.04m. Wheels are positioned at x=±0.1m, y=±0.175m from chassis center.
