import math
import time
from fpv_lab2.flight_state import FlightState

class NavigateHandler:
    def __init__(self, node):
        self.node = node

    def execute(self):
        self.node.publish_target_pose(
            self.node.target_x, 
            self.node.target_y, 
            self.node.target_z
        )

        distance = math.sqrt(
            (self.node.current_x - self.node.target_x) ** 2 +
            (self.node.current_y - self.node.target_y) ** 2
        )

        self.node.get_logger().info(
            f'Navigating to. Distance: {distance:.2f} m',
            throttle_duration_sec=1.0
        )

        if distance <= self.node.tolerance:
            self.node.get_logger().info(
                f'Target reached! Stopping and hovering for {self.node.hover_duration} seconds.'
            )
            self.node.hover_start_time = time.time()
            self.node.state = FlightState.HOVERING
