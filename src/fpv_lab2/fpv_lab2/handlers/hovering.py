
import time
from typing import TYPE_CHECKING

from ..flight_state import FlightState
from .handler import FlightStateHandler

if TYPE_CHECKING:
    from ..flight_test_node import FlightTestNode


class HoveringHandler(FlightStateHandler):
    def handle(self, node: "FlightTestNode") -> None:
        if node.takeoff_started_at is None:
            return

        if node.status is None:
            return

        elapsed_since_takeoff = (
            time.monotonic() - node.takeoff_started_at
        )

        if not node.status.armed:
            if elapsed_since_takeoff < 5.0:
                return

            node.fail("Drone disarmed unexpectedly during takeoff")
            return

        if node.odometry is None:
            return

        altitude = node.odometry.pose.pose.position.z

        if node.hover_started_at is None:
            if altitude < node.TAKEOFF_ALTITUDE - 0.25:
                node.get_logger().info(
                    f"Climbing: altitude={altitude:.2f} m",
                    throttle_duration_sec=1.0,
                )
                return

            node.hover_started_at = time.monotonic()
            node.get_logger().info(
                f"Target altitude reached. Hovering for "
                f"{node.HOVER_DURATION:.1f} seconds"
            )
            return

        elapsed = time.monotonic() - node.hover_started_at

        node.get_logger().info(
            f"Hovering: altitude={altitude:.2f} m",
            throttle_duration_sec=2.0,
        )

        if elapsed >= node.HOVER_DURATION:
            node.get_logger().info(
                "Hover completed, starting next stage"
            )
            node.state = FlightState.NAVIGATING_TO_TARGET
