# Bugs Found & Fixes (Claude session log)

### 1. Map drift: wheel-odom-only setup yielded warped SLAM maps
**Symptom**: saved `house_map.pgm` had sheared/doubled walls; robot position on the map diverged from its position in Gazebo over time; Nav2 planning occasionally failed from what looked like free space.
**Cause**: `odom → base_link` was published by `diff_drive_controller` using only wheel ticks. Differential drives accumulate unbounded yaw error from tire slip, and slam_toolbox's 1°-resolution scan matching couldn't correct it fully between loop closures.
**Fix**: added IMU (`imu.xacro` + `gz-sim-imu-system` in worlds + `/imu` bridge) and a `robot_localization` EKF (`config/ekf.yaml`) fusing **wheel vx** + **IMU vyaw**. Set `enable_odom_tf: false` on `diff_drive_controller` so the EKF is the sole publisher of `odom → base_link`. Pointed Nav2's `odom_topic` at `/odometry/filtered` in `nav2_params.yaml`.

### 2. Controller activation hung with "Switch controller timed out after 5 seconds"
**Symptom**: after adding the IMU, `joint_state_broadcaster` activation timed out; Gazebo then exited cleanly.
**Cause**: `gz_ros2_control` auto-discovered the IMU `<sensor>` in the URDF but had no matching `<sensor>` declaration inside `<ros2_control>`, so it registered an empty sensor resource — which then stalled controller activation.
**Fix**: added a `<sensor name="imu_sensor">` block to `ros2_control.xacro` with the 10 standard IMU state_interfaces (orientation xyzw, angular_velocity xyz, linear_acceleration xyz). Also explicitly scoped `joint_state_broadcaster` in `controllers.yaml` to the four wheel joints so it doesn't try to publish the IMU's interfaces.

### 3. IMU topic silent even with sensor declared
**Symptom**: `/imu` topic appeared in the topic list but produced no data, and `ros_gz_bridge` was logging-only.
**Cause**: the world files loaded `gz-sim-sensors-system` (handles lidar) but not `gz-sim-imu-system`. IMU sensors in Gazebo Harmonic require their own system plugin.
**Fix**: added `<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>` to both `house.world` and `empty.world`.

### 4. Stationary robot showed ~1 m position drift on `/odometry/filtered`
**Symptom**: robot motionless in Gazebo, but EKF reported position ≈ (0, -0.87) m and covariance ≈ 3000 on y.
**Cause**: initial EKF config fused IMU `ax`, `ay` along with `vyaw`. The Gazebo IMU reports orientation covariance of 0 and noisy accel; integrating noisy accel on a stationary robot diverges fast.
**Fix**: narrowed `imu0_config` in `ekf.yaml` to `vyaw` only and set `imu0_remove_gravitational_acceleration: false`. Result: stationary robot now reads (~0, ~0) on `/odometry/filtered`.

### 5. Nav2 planner couldn't find a plan from (0, 0) to (3.2, -1.7)
**Symptom**: `GridBased plugin failed to plan from (-0.00, -0.00) to (3.20, -1.70): "Failed to create plan with tolerance of: 0.500000"` in a tight retry loop; spin + backup recoveries both failed immediately.
**Cause**: compounded by bug #1 — the saved map was warped and AMCL seeded at (0, 0) happened to land inside the inflated costmap. Once the EKF fix was in place and odom was honest, the planner began finding paths.
**Fix**: installing the EKF (bug #1) resolved the majority of planning failures. Saved-map quality is still a limiting factor; re-SLAM with EKF enabled to eliminate the residual map-vs-world offset.

### 6. "Failed to make progress" — robot wouldn't move even with a valid plan
**Symptom**: `bt_navigator` accepted the goal, planner returned a path, but `controller_server` logged "Failed to make progress" repeatedly. Robot stayed at origin. `/diff_drive_controller/cmd_vel` reported having **both** `Twist` and `TwistStamped` publisher/subscriber types.
**Cause**: Nav2's `controller_server` publishes `geometry_msgs/Twist`, but Jazzy's `diff_drive_controller` subscribes to `geometry_msgs/TwistStamped`. The `use_stamped_vel: false` parameter in `controllers.yaml` appears to be ignored in this version — the controller subscribes to stamped regardless. Type mismatch → messages silently dropped → robot never moves.
**Fix**: added `scripts/cmd_vel_relay.py`, a tiny node that subscribes to `/cmd_vel_nav` (Twist) and republishes to `/diff_drive_controller/cmd_vel` (TwistStamped) with a fresh sim-time stamp. Installed via `CMakeLists.txt`. In `sim_nav.launch.py`, `controller_server`'s `cmd_vel` is now remapped to `/cmd_vel_nav` and `cmd_vel_relay` is added to the launch description. Also updated `sim_teleop.launch.py` to publish unstamped (consistent with Nav2's output style).

### 7. AMCL seeded at (0, 0) but robot visually at a different spot on the map
**Symptom**: robot icon on the map in RViz didn't match where the robot was in Gazebo.
**Cause**: the saved `house_map.pgm` was built before the EKF fix (bug #1), so the map's origin doesn't correspond exactly to the Gazebo world origin. AMCL honors its `set_initial_pose` config at (0, 0) regardless.
**Fix (workaround)**: use RViz "2D Pose Estimate" to click the actual robot location after launch. **Permanent fix**: re-run `sim_slam.launch.py` with the new EKF setup, revisit at least one room for loop closure, then re-save the map.

### 8. Launch-file refactor introduced `'DeclareLaunchArgument' object is not iterable`
**Symptom**: `sim_nav.launch.py` shut down immediately after `Managed nodes are active` with `TypeError: 'DeclareLaunchArgument' object is not iterable` coming out of `ResetLaunchConfigurations.execute()`.
**Cause**: a draft version of the launch file used `OpaqueFunction` inside `TimerAction.actions` to publish an `/initialpose` message with launch-arg-derived quaternion math. That nesting doesn't round-trip through the launch framework's scope-reset handling in Jazzy.
**Fix**: reverted the dynamic initial-pose publisher — AMCL's `set_initial_pose: true` in `nav2_params.yaml` already handles the seed adequately. For manual overrides, use RViz "2D Pose Estimate".
