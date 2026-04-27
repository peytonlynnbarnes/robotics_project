#!/usr/bin/env python3
"""stepper_odom.py — ROS 2 odometry publisher, driven by /stepper step counts.

Subscribes to /stepper (std_msgs/Int32MultiArray) published by stepper_driver.
  data[0] = left  wheel signed steps since last message
  data[1] = right wheel signed steps since last message

Publishes
  /odom            (nav_msgs/Odometry)    — consumed by robot_localization EKF
  /joint_states    (sensor_msgs/JointState) — wheel angles for RViz

No GPIO access — all hardware interaction is owned by stepper_driver.
"""

import math
import threading

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Quaternion
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from std_msgs.msg import Int32


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def euler_to_quaternion(yaw: float) -> Quaternion:
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class StepperOdomNode(Node):

    def __init__(self):
        super().__init__('stepper_odom')

        # ---- parameters -------------------------------------------------------
        self.declare_parameter('wheel_diameter',  0.075)
        self.declare_parameter('wheelbase',       0.270)
        self.declare_parameter('steps_per_rev',   200)
        self.declare_parameter('publish_rate',    50.0)
        self.declare_parameter('odom_frame',      'odom')
        self.declare_parameter('base_frame',      'base_link')

        wheel_diameter      = self.get_parameter('wheel_diameter').value
        self._wheelbase     = self.get_parameter('wheelbase').value
        steps_per_rev       = self.get_parameter('steps_per_rev').value
        publish_rate        = self.get_parameter('publish_rate').value
        self._odom_frame    = self.get_parameter('odom_frame').value
        self._base_frame    = self.get_parameter('base_frame').value

        self._wheel_circ      = math.pi * wheel_diameter
        self._metres_per_step = self._wheel_circ / steps_per_rev
        self._steps_per_rev   = steps_per_rev

        # ---- robot pose state -------------------------------------------------
        self._lock        = threading.Lock()
        self._x           = 0.0
        self._y           = 0.0
        self._yaw         = 0.0
        self._left_angle  = 0.0
        self._right_angle = 0.0
        self._v_linear    = 0.0
        self._v_angular   = 0.0
        self._last_time   = self.get_clock().now()

        # ---- latest step counts (written by sub callbacks, read by timer) ----
        self._left_steps_buf  = 0
        self._right_steps_buf = 0

        # ---- subscribers -------------------------------------------------------
        self._left_sub = self.create_subscription(
            Int32, '/stepperLeft', self._left_cb, 10
        )
        self._right_sub = self.create_subscription(
            Int32, '/stepperRight', self._right_cb, 10
        )

        # ---- publishers -------------------------------------------------------
        self._odom_pub  = self.create_publisher(Odometry,   '/odom',         10)
        self._joint_pub = self.create_publisher(JointState, '/joint_states',  10)

        self.create_timer(1.0 / publish_rate, self._publish_cb)

        self.get_logger().info(
            f'stepper_odom ready — '
            f'{steps_per_rev} steps/rev, '
            f'wheel ⌀ {wheel_diameter*1000:.0f} mm, '
            f'wheelbase {self._wheelbase*1000:.0f} mm'
        )

    # -------------------------------------------------------------------------
    # /stepperLeft and /stepperRight callbacks
    # -------------------------------------------------------------------------

    def _left_cb(self, msg: Int32):
        with self._lock:
            self._left_steps_buf = int(msg.data)
        self._integrate()

    def _right_cb(self, msg: Int32):
        with self._lock:
            self._right_steps_buf = int(msg.data)
        self._integrate()

    def _integrate(self):
        """Integrate whatever step counts are currently buffered into pose.

        Called on every incoming message from either wheel. Because the two
        topics are published independently, we integrate each new count
        immediately rather than waiting for both to arrive together.
        """
        now = self.get_clock().now()

        with self._lock:
            left_steps  = self._left_steps_buf
            right_steps = self._right_steps_buf
            self._left_steps_buf  = 0
            self._right_steps_buf = 0

            if left_steps == 0 and right_steps == 0:
                return

            d_left  = left_steps  * self._metres_per_step
            d_right = right_steps * self._metres_per_step

            d_centre = (d_right + d_left)  / 2.0
            d_yaw    = (d_right - d_left)  / self._wheelbase

            dt = (now - self._last_time).nanoseconds * 1e-9
            self._last_time = now

            self._yaw += d_yaw
            self._x   += d_centre * math.cos(self._yaw)
            self._y   += d_centre * math.sin(self._yaw)

            self._left_angle  += (2.0 * math.pi * left_steps)  / self._steps_per_rev
            self._right_angle += (2.0 * math.pi * right_steps) / self._steps_per_rev

            if dt > 0.0:
                self._v_linear  = d_centre / dt
                self._v_angular = d_yaw    / dt

    # -------------------------------------------------------------------------
    # Publish timer — /odom, TF, /joint_states at publish_rate Hz
    # -------------------------------------------------------------------------

    def _publish_cb(self):
        now = self.get_clock().now()

        with self._lock:
            x           = self._x
            y           = self._y
            yaw         = self._yaw
            v_linear    = self._v_linear
            v_angular   = self._v_angular
            left_angle  = self._left_angle
            right_angle = self._right_angle

        # ---- Odometry --------------------------------------------------------
        odom = Odometry()
        odom.header.stamp    = now.to_msg()
        odom.header.frame_id = self._odom_frame
        odom.child_frame_id  = self._base_frame

        odom.pose.pose.position.x  = x
        odom.pose.pose.position.y  = y
        odom.pose.pose.position.z  = 0.0
        odom.pose.pose.orientation = euler_to_quaternion(yaw)

        odom.twist.twist.linear.x  = v_linear
        odom.twist.twist.angular.z = v_angular

        # Pose covariance (row/col order: x, y, z, roll, pitch, yaw).
        # EKF fuses odom0_config vx only — pose covariance is informational.
        odom.pose.covariance[0]  = 0.001   # x
        odom.pose.covariance[7]  = 0.001   # y
        odom.pose.covariance[14] = 1e6     # z     (planar — unused)
        odom.pose.covariance[21] = 1e6     # roll  (unused)
        odom.pose.covariance[28] = 1e6     # pitch (unused)
        odom.pose.covariance[35] = 1e6     # yaw   — EKF ignores, IMU owns this

        # Twist covariance — EKF fuses vx only (index 0).
        # vyaw (index 35) set very high so EKF ignores it; IMU gyro owns yaw rate.
        odom.twist.covariance[0]  = 0.001  # vx  ← only value EKF actually uses
        odom.twist.covariance[7]  = 1e6    # vy  (non-holonomic — unused)
        odom.twist.covariance[35] = 1e6    # vyaw — ignored, IMU owns it

        self._odom_pub.publish(odom)

        # TF NOT broadcast here — ekf.yaml has publish_tf: true so EKF
        # is the sole publisher of odom → base_link.

        # ---- JointState (RViz wheel rendering) --------------------------------
        wheel_radius = self._wheel_circ / (2.0 * math.pi)
        js = JointState()
        js.header.stamp = now.to_msg()
        js.name     = ['left_wheel_joint', 'right_wheel_joint']
        js.position = [left_angle, right_angle]
        js.velocity = [v_linear / wheel_radius, v_linear / wheel_radius]
        self._joint_pub.publish(js)


# ---------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = StepperOdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
    