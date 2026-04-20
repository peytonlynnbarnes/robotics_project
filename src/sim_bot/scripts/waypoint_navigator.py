#!/usr/bin/env python3
"""Navigate to named rooms via /go_to_room topic."""
import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import String


class WaypointNavigator(Node):
    def __init__(self):
        super().__init__('waypoint_navigator')

        self.declare_parameter('waypoint_names', [''])
        names = (
            self.get_parameter('waypoint_names')
            .get_parameter_value()
            .string_array_value
        )

        self.waypoints = {}
        for name in names:
            if not name:
                continue
            self.declare_parameter(f'{name}.x', 0.0)
            self.declare_parameter(f'{name}.y', 0.0)
            self.declare_parameter(f'{name}.yaw', 0.0)
            self.waypoints[name] = {
                'x': self.get_parameter(f'{name}.x').value,
                'y': self.get_parameter(f'{name}.y').value,
                'yaw': self.get_parameter(f'{name}.yaw').value,
            }

        self.get_logger().info(f'Loaded waypoints: {list(self.waypoints.keys())}')

        self._action_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose'
        )
        self._current_goal = None

        self.create_subscription(String, '/go_to_room', self._on_command, 10)

    def _on_command(self, msg):
        room = msg.data.strip().lower()
        if room not in self.waypoints:
            self.get_logger().warn(
                f'Unknown room "{room}". '
                f'Available: {list(self.waypoints.keys())}'
            )
            return

        if self._current_goal is not None:
            self.get_logger().info('Canceling current goal')
            self._current_goal.cancel_goal_async()

        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('NavigateToPose action server not available')
            return

        wp = self.waypoints[room]
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = wp['x']
        goal.pose.pose.position.y = wp['y']
        goal.pose.pose.orientation.z = math.sin(wp['yaw'] / 2.0)
        goal.pose.pose.orientation.w = math.cos(wp['yaw'] / 2.0)

        self.get_logger().info(
            f'Navigating to {room} ({wp["x"]:.1f}, {wp["y"]:.1f})'
        )
        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: self._on_goal_response(f, room)
        )

    def _on_goal_response(self, future, room):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn(f'Goal to {room} rejected')
            return

        self._current_goal = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda f: self._on_result(f, room)
        )

    def _on_result(self, future, room):
        status = future.result().status
        self._current_goal = None
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f'Arrived at {room}!')
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().info(f'Navigation to {room} canceled')
        else:
            self.get_logger().error(f'Failed to reach {room} (status={status})')


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(WaypointNavigator())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
