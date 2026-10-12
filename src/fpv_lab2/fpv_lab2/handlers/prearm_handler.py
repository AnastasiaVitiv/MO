import time
from fpv_lab2.flight_state import FlightState

class PrearmHandler:
    def __init__(self, node):
        self.node = node
        self.future = None
        self.last_retry_time = 0.0

    def execute(self):
        current_time = time.time()
      if current_time - self.last_retry_time < 2.0:
            return

        self.last_retry_time = current_time
        self.node.get_logger().info('Checking if vehicle is armable...')
      if not self.node.arm_client.service_is_ready():
            self.node.get_logger().info('Waiting for ArduPilot arm service...')
            return

        req = self.node.arm_client.Request() if hasattr(self.node.arm_client, 'Request') else None
      from std_srvs.srv import Trigger
        req = Trigger.Request()

        future = self.node.arm_client.call_async(req)
      try:
            rclpy_spin_once_timeout = 0.1
            if future.done():
                res = future.result()
                if res.success:
                    self.node.get_logger().info('Pre-arm check passed: Vehicle is Armable')
                    self.node.state = FlightState.SETTING_GUIDED
                else:
                    self.node.get_logger().warn('Vehicle is not armable yet, retrying...')
        except Exception:
            pass
