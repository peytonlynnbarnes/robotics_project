# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS2 differential drive robot simulation ("sim_bot") using Gazebo. Four-wheeled robot with paired left/right differential drive control via ros2_control. Equipped with a 360° 2D lidar feeding `slam_toolbox` for online SLAM, and a MEMS IMU fused with wheel odometry via `robot_localization` EKF for low-drift pose estimation.

**Stack**: ROS 2 Jazzy + Gazebo Harmonic (gz-sim 8) on Ubuntu 24.04. Plugin/sensor types must use the `gz` (not `ignition`) namespace.

## Prerequisites

```bash
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-robot-localization ros-jazzy-nav2-bringup xterm
```
- `slam_toolbox` — required by `sim_slam.launch.py`.
- `robot_localization` — required by `sim_gazebo.launch.py` (EKF).
- `nav2-bringup` — pulls in the Nav2 stack used by `sim_nav.launch.py`.
- `xterm` — required by `sim_teleop.launch.py` (teleop_twist_keyboard needs a TTY for keystrokes).

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

# Save the map after mapping (do it immediately — don't drive further)
ros2 run nav2_map_server map_saver_cli -f src/sim_bot/maps/house_map

# Sim + Nav2 stack + RViz
ros2 launch sim_bot sim_nav.launch.py
# Send robot to a named room
ros2 topic pub --once /go_to_room std_msgs/msg/String "{data: 'kitchen'}"

# Manual cmd_vel (TwistStamped — diff_drive_controller subscribes to stamped only in Jazzy)
ros2 topic pub /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  "{header: {frame_id: '', stamp: {sec: 0, nanosec: 0}}, twist: {linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.3}}}" -r 10

# Kill all simulation processes
pkill -f "gz sim|ros2 launch|slam_toolbox|rviz2|controller_manager|robot_state_publisher|spawner|ekf_node|waypoint_navigator|cmd_vel_relay|parameter_bridge|lifecycle_manager|amcl|bt_navigator|planner_server|controller_server|behavior_server|map_server"
```

## Architecture

### Package: sim_bot (`src/sim_bot/`)

Build system: ament_cmake via colcon. Python nodes under `scripts/`:
- `waypoint_navigator.py` — subscribes to `/go_to_room`, looks up coords in `waypoints.yaml`, dispatches `NavigateToPose` action goals.
- `cmd_vel_relay.py` — converts Nav2's `geometry_msgs/Twist` output to `geometry_msgs/TwistStamped` with a fresh sim-time header (Nav2 publishes unstamped; Jazzy's `diff_drive_controller` subscribes to stamped).

**Robot description** (`description/`): Xacro files composing the URDF.
- `robot.urdf.xacro` — top-level, includes all others and instantiates each macro
- `robot_core.xacro` — chassis (0.3×0.3×0.25 m) and 4 wheel joints
- `ros2_control.xacro` — hardware interface definitions: velocity command + position/velocity state per wheel, **and** an `imu_sensor` element with 10 state_interfaces (orientation xyzw, angular_velocity xyz, linear_acceleration xyz) so `gz_ros2_control` can bind the Gazebo IMU cleanly
- `gazebo_control_plugin.xacro` — gz_ros2_control plugin bridge
- `lidar.xacro` — `laser_frame` link mounted on top of chassis + `gpu_lidar` Gazebo sensor
- `imu.xacro` — `imu_link` on the chassis + Gazebo `<sensor type="imu">` publishing to `/imu` at 100 Hz (gyro σ=0.0003 rad/s, accel σ=0.017 m/s²)
- `inertial_macros.xacro` — reusable inertia calculators (sphere, box, cylinder)

**Control pipeline**: Gazebo physics → `gz_ros2_control/GazeboSimSystem` → controller_manager (100 Hz) → `diff_drive_controller` + `joint_state_broadcaster`. `diff_drive_controller` has `enable_odom_tf: false` — it publishes `/diff_drive_controller/odom` as a topic only; the `odom → base_link` TF is owned by `robot_localization`. `joint_state_broadcaster` is **scoped to the four wheel joints** (position + velocity interfaces) so the IMU's 10 sensor interfaces don't get published on `/joint_states`.

**State-estimation pipeline** (`config/ekf.yaml`):
```
  /diff_drive_controller/odom ──┐
                                ├──▶ robot_localization (ekf_filter_node) ──▶ /odometry/filtered
  /imu ─────────────────────────┘                                        └──▶ TF: odom → base_link
```
EKF is in 2D mode, 30 Hz. Fuses **wheel vx** (trusted for linear velocity) + **IMU vyaw** (gyro-z, trusted for angular velocity). Orientation and linear acceleration from the IMU are intentionally NOT fused — the Gazebo IMU reports zero orientation covariance which confuses the filter, and integrating noisy accel at rest introduces drift. This is the canonical diff-drive recipe.

**Nav2 velocity pipeline** (`sim_nav.launch.py`):
```
  Nav2 controller_server (publishes Twist to /cmd_vel) ──[remap]──▶ /cmd_vel_nav
                                                                        │
                                                   cmd_vel_relay (Twist → TwistStamped,
                                                   stamps header with sim time)
                                                                        │
                                                                        ▼
                                           /diff_drive_controller/cmd_vel (TwistStamped)
                                                                        │
                                                                        ▼
                                                             diff_drive_controller
```
Why the relay exists: Jazzy's `diff_drive_controller` subscribes to `TwistStamped` regardless of `use_stamped_vel` (the param appears to be ignored). Nav2 always publishes unstamped `Twist`. Without the relay, topic types don't match and the robot never moves despite successful planning ("Failed to make progress" loops).

**Launch sequence** (`launch/sim_gazebo.launch.py`): Gazebo → clock bridge → lidar bridge → IMU bridge → robot_state_publisher → spawn entity → joint_state_broadcaster → diff_drive_controller → `ekf_node`. Each controller spawns after the previous via event handlers.

**Composite launches**:
- `sim_teleop.launch.py` — `sim_gazebo` + `teleop_twist_keyboard` (xterm prefix, `stamped:=False`, remapped to `/diff_drive_controller/cmd_vel`)
- `sim_slam.launch.py` — `sim_gazebo` + `async_slam_toolbox_node` (lifecycle: auto-configure+activate) + `rviz2` (loads `config/slam.rviz`)
- `sim_full.launch.py` — `sim_gazebo` + SLAM + RViz (no teleop)
- `sim_nav.launch.py` — `sim_gazebo` + Nav2 stack (map_server, AMCL, planner, controller, BT navigator, behavior server, lifecycle_manager) + `cmd_vel_relay` + `waypoint_navigator` + RViz (loads `config/nav.rviz`). Accepts `map:=<path>` argument.

**World files** (`worlds/`):
- `empty.world` — bare ground plane. Loads `gz-sim-sensors-system` + `gz-sim-imu-system`.
- `house.world` — 10×8 m house with 4 rooms (living room, kitchen, bedroom, bathroom), central hallway, and furniture. Loads `gz-sim-sensors-system` + `gz-sim-imu-system`. Default world for `sim_gazebo.launch.py`; override with `world:=empty.world`.

Both worlds **must** load `gz-sim-imu-system`, or the IMU sensor in the URDF produces no data and `gz_ros2_control` hangs controller activation.

**Controller config** (`config/controllers.yaml`):
- Diff drive: `wheel_separation=0.35 m`, `wheel_radius=0.08255 m`, `publish_rate=50 Hz`.
- Left wheels: `[left_front_wheel_joint, left_rear_wheel_joint]`, right: `[right_front_wheel_joint, right_rear_wheel_joint]`.
- `base_frame_id: base_link` — standard ROS convention. slam_toolbox and Nav2 both reference this.
- `enable_odom_tf: false` — EKF owns the TF.
- `use_stamped_vel: false` — note: appears to be ignored in Jazzy; controller still subscribes to `TwistStamped`. Kept for documentation; the `cmd_vel_relay` node is what actually bridges the type gap.
- `joint_state_broadcaster` is explicitly scoped to the four wheel joints (position + velocity) to avoid claiming the IMU's state interfaces.

### Sensors

**Lidar** (`description/lidar.xacro`): 360° 2D lidar mounted on top of chassis at `xyz="0 0 0.27"` (≈0.32 m above ground). 360 samples, 0.12–12 m range, 10 Hz, gaussian noise σ=0.01 m. Defined as `gpu_lidar` sensor with `<gz_frame_id>laser_frame</gz_frame_id>` so the published `LaserScan.header.frame_id` matches the URDF link. Bridged Gazebo→ROS by `lidar_bridge` in `sim_gazebo.launch.py` as `/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan`.

**IMU** (`description/imu.xacro`): 6-axis IMU (gyro + accel) on `imu_link` at `xyz="0 0 0.05"` on the chassis. 100 Hz update rate, gyro noise σ=0.0003 rad/s, accel noise σ=0.017 m/s². Bridged Gazebo→ROS by `imu_bridge` in `sim_gazebo.launch.py` as `/imu@sensor_msgs/msg/Imu[gz.msgs.IMU`. Also declared as a `<sensor>` inside the `<ros2_control>` block so `gz_ros2_control` can register its state interfaces.

### SLAM

`slam_toolbox` async online mode, configured in `config/slam_params.yaml`. In ROS 2 Jazzy, slam_toolbox is a **lifecycle node** — launch files must configure and activate it (see `sim_slam.launch.py` for the pattern). The EKF (`ekf_node`) provides `odom → base_link`; slam_toolbox produces `map → odom`. **`base_frame: base_link`** in `slam_params.yaml` must match the controller's `base_frame_id` or TF resolution will fail.

Because the EKF fuses IMU yaw, the `odom → base_link` transform is much less drifty than raw wheel odometry — this directly improves slam_toolbox's scan matching quality and the resulting saved map.

### Navigation (Nav2)

`sim_nav.launch.py` launches the full Nav2 stack for autonomous navigation to named rooms. Requires a saved map (run SLAM first, then `ros2 run nav2_map_server map_saver_cli -f src/sim_bot/maps/house_map`).

- `waypoint_navigator` subscribes to `/go_to_room` (std_msgs/String), looks up coords in `config/waypoints.yaml`, sends NavigateToPose action goals.
- Nav2's `controller_server` publishes `/cmd_vel` (Twist), remapped in the launch file to `/cmd_vel_nav`, which `cmd_vel_relay` then republishes as `/diff_drive_controller/cmd_vel` (TwistStamped).
- Nav2 consumes `/odometry/filtered` (the fused EKF output) for its local planner — see `odom_topic` in `config/nav2_params.yaml`.
- AMCL config has `set_initial_pose: true` with `(0, 0, 0)` so the filter seeds at the Gazebo spawn pose on startup. If you mapped badly and the saved map's origin doesn't match spawn, use RViz's "2D Pose Estimate" to re-seed.

### Package: face_recognition (`src/face_recognition/`)

Placeholder — currently empty.

## Key ROS2 Topics

- `/diff_drive_controller/cmd_vel` (**TwistStamped**) — velocity input to the controller (published by `cmd_vel_relay` in nav, by teleop in manual driving)
- `/cmd_vel_nav` (Twist) — Nav2's raw controller_server output, consumed by `cmd_vel_relay`
- `/diff_drive_controller/odom` (Odometry) — wheel odometry (topic-only; no TF)
- `/imu` (Imu) — IMU data from Gazebo, 100 Hz
- `/odometry/filtered` (Odometry) — EKF-fused odometry; publishes `odom → base_link` TF
- `/joint_states` — wheel positions/velocities (scoped to wheel joints only)
- `/scan` (LaserScan) — lidar output, frame_id `laser_frame`
- `/map` (OccupancyGrid) — slam_toolbox or map_server output
- `/go_to_room` (String) — send room name to waypoint_navigator (e.g. "kitchen")
- `/tf`, `/tf_static` — transform tree: `map → odom → base_link → chassis → {wheels, laser_frame, imu_link}`

## Wheel Geometry

Left wheels rotate along Z=+1, right wheels along Z=-1. Wheel radius=0.08255 m, width=0.04 m. Wheels are positioned at x=±0.1 m, y=±0.175 m from chassis center.

## Bug history

See [`BUGS.md`](BUGS.md) for a log of bugs found and fixes applied during Claude sessions — useful context when something breaks in a way that looks familiar.
