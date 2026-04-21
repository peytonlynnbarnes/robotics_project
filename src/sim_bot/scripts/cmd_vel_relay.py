#!/usr/bin/env python3
"""Republishes /cmd_vel_nav (Twist) as /diff_drive_controller/cmd_vel (TwistStamped).

Nav2's controller_server publishes Twist; Jazzy's diff_drive_controller subscribes
to TwistStamped. This bridges the two with a fresh sim-time stamp.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped


class CmdVelRelay(Node):
    def __init__(self):
        super().__init__('cmd_vel_relay')
        self.pub = self.create_publisher(
            TwistStamped, '/diff_drive_controller/cmd_vel', 10)
        self.sub = self.create_subscription(
            Twist, '/cmd_vel_nav', self.cb, 10)

    def cb(self, msg: Twist):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.twist = msg
        self.pub.publish(out)


def main():
    rclpy.init()
    rclpy.spin(CmdVelRelay())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
