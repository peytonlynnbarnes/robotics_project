from gpiozero import OutputDevice
from time import sleep
import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Int32
from geometry_msgs.msg import Twist

totalStep = 0

# iiigpiozero uses BCM numbering (not BOARD)
DIR = 24    # BOARD 31 → BCM 6
STEP = 23   # BOARD 29 → BCM 5

CW = 0
CCW = 1

# Initialize pins
dir_pin = OutputDevice(DIR)
step_pin = OutputDevice(STEP)

print("Running")

class MotorSubscriber(Node):

    def __init__(self):
        super().__init__('minimal_subscriber')

        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.listener_callback,
            10
        )

        self.linear_vel = 0
        self.angular_vel = 0

        self.timer = self.create_timer(0.01, self.controlLoop)
        self.stepper_timer = self.create_timer(1.0/50.0, self.publish_step)

        self.stepper_pub = self.create_publisher(Int32, 'stepperRight', 10)

    def publish_step(self):
        msg = Int32()
        msg.data = totalStep
        self.stepper_pub.publish(msg)

    def listener_callback(self, msg):
        self.linear_vel = msg.linear.x
        self.angular_vel = msg.angular.z
        print(self.angular_vel)

    def controlLoop(self):
        pwm_time, direction = computeSpeed(self.linear_vel, self.angular_vel, "right")
        step(2, direction, pwm_time, 0)


def computeSpeed(linear, angular, motor):
    wheel_sep = 4
    wheel_diameter = 0.075
    stepsPerRev = 200

    if motor == "left":
        speed = linear + angular * wheel_sep / 2
    else:
        speed = linear - angular * wheel_sep / 2

    print("Right: ", speed)

    direction = CW
    if speed < 0:
        direction = CCW
        speed = abs(speed)

    if speed < 0.0001:
        PWM_time = 10
    else:
        PWM_time = math.pi * wheel_diameter / (2 * speed * stepsPerRev)

    return PWM_time, direction


def step(numStep, direction, PWM_SPEED, space_time):
    global totalStep
    dirMult = 1
    # Set direction
    if direction == CW:
        dir_pin.off()
    else:
        dirMult=-1
        dir_pin.on()

    if PWM_SPEED < 0.5:
        for _ in range(numStep):
            step_pin.on()
            sleep(PWM_SPEED)

            step_pin.off()
            sleep(PWM_SPEED)

            sleep(space_time)
            totalStep += 1*dirMult
    else:
        step_pin.off()


def main(args=None):
    rclpy.init(args=args)
    node = MotorSubscriber()

    try:
        rclpy.spin(node)
    finally:
        print("Shutting down...")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
