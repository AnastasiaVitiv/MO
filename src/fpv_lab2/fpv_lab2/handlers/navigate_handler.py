
import math
import time

from geometry_msgs.msg import TwistStamped

from ..flight_state import FlightState
from .handler import FlightStateHandler


class NavigateHandler(FlightStateHandler):
    def __init__(self):
        self.last_log_time = 0.0

    def handle(self, node) -> None:
        if (
            node.odometry is None
            or node.target_x is None
            or node.target_y is None
        ):
            return

        pose = node.odometry.pose.pose
        position = pose.position

        dx = node.target_x - position.x
        dy = node.target_y - position.y
        distance = math.hypot(dx, dy)

        if distance <= node.target_tolerance:
            self.publish_velocity(node, 0.0, 0.0)

            error = math.hypot(
                position.x - node.target_x,
                position.y - node.target_y,
            )

            node.get_logger().info(
                f"Actual position: ({position.x:.2f}, {position.y:.2f})"
            )
            node.get_logger().info(
                f"Target position: ({node.target_x:.2f}, "
                f"{node.target_y:.2f})"
            )
            node.get_logger().info(
                f"Position error: {error:.3f} m"
            )
            node.get_logger().info(
                "Target reached, starting landing"
            )

            node.state = FlightState.LANDING
            return

        speed = min(
            node.max_navigation_speed,
            node.navigation_gain * distance,
        )

        vx_world = speed * dx / distance
        vy_world = speed * dy / distance

        q = pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )

        vx_body = (
            math.cos(yaw) * vx_world
            + math.sin(yaw) * vy_world
        )
        vy_body = (
            -math.sin(yaw) * vx_world
            + math.cos(yaw) * vy_world
        )

        self.publish_velocity(node, vx_body, vy_body)

        now = time.monotonic()
        if now - self.last_log_time >= 1.0:
            node.get_logger().info(
                f"Navigating: distance={distance:.2f} m, "
                f"speed={speed:.2f} m/s"
            )
            self.last_log_time = now

    def publish_velocity(self, node, vx, vy):
        message = TwistStamped()

        message.header.stamp = node.get_clock().now().to_msg()
        message.header.frame_id = "base_link"

        message.twist.linear.x = float(vx)
        message.twist.linear.y = float(vy)
        message.twist.linear.z = 0.0

        message.twist.angular.x = 0.0
        message.twist.angular.y = 0.0
        message.twist.angular.z = 0.0

        node.cmd_vel_publisher.publish(message)
