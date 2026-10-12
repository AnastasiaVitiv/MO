import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry

from fpv_lab2.flight_state import FlightState
from fpv_lab2.handlers.prearm_handler import PrearmHandler
from fpv_lab2.handlers.guided_handler import GuidedHandler
from fpv_lab2.handlers.arm_handler import ArmHandler
from fpv_lab2.handlers.takeoff_handler import TakeoffHandler
from fpv_lab2.handlers.navigate_handler import NavigateHandler
from fpv_lab2.handlers.hover_handler import HoverHandler
from fpv_lab2.handlers.land_handler import LandHandler
class FlightTestNode(Node):
    def __init__(self):
        super().__init__('flight_test')

        self.state = FlightState.WAITING_FOR_SYSTEM

        self.delta_x = 7.0        
        self.delta_y = -0.5       
        self.target_z = 2.0       
        self.tolerance = 0.3
        self.hover_duration = 5.0  
        self.start_pose_saved = False
        self.x0 = 0.0
        self.y0 = 0.0
        self.target_x = 0.0
        self.target_y = 0.0

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.hover_start_time = None

        self.target_pose_pub = self.create_publisher(
            PoseStamped, 
            '/ardupilot/setpoint_pose/plugin', 
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/ardupilot/odometry',
            self.odom_callback,
            10
        )
        self.handlers = {
            FlightState.PREARM_CHECK: PrearmHandler(self),
            FlightState.SETTING_GUIDED: GuidedHandler(self),
            FlightState.ARMING: ArmHandler(self),
            FlightState.TAKING_OFF: TakeoffHandler(self),
            FlightState.NAVIGATING_TO_TARGET: NavigateHandler(self),
            FlightState.HOVERING: HoverHandler(self),
            FlightState.LANDING: LandHandler(self),
        }

        self.timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('Flight test node for Variant 29 initialized')

    def odom_callback(self, msg: Odometry):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        self.current_z = msg.pose.pose.position.z

        if not self.start_pose_saved:
            self.x0 = self.current_x
            self.y0 = self.current_y
            self.target_x = self.x0 + self.delta_x
            self.target_y = self.y0 + self.delta_y
            self.start_pose_saved = True
            self.get_logger().info(
                f'Start pose: ({self.x0:.2f}, {self.y0:.2f}). '
                f'Target pose (Var 29): ({self.target_x:.2f}, {self.target_y:.2f})'
            )

    def publish_target_pose(self, x, y, z):
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = 'map'
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = float(z)
        self.target_pose_pub.publish(pose)

    def control_loop(self):
        if self.state == FlightState.WAITING_FOR_SYSTEM:
            if self.start_pose_saved:
                self.state = FlightState.PREARM_CHECK
            return

        if self.state == FlightState.FINISHED:
            self.get_logger().info('Mission completed. Shutting down node.')
            rclpy.shutdown()
            return

        if self.state in self.handlers:
            self.handlers[self.state].execute()
