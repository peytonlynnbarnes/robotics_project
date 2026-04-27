#handsontec.com/dataspecs/motor_fan/MGR996R.pdf
from time import sleep
import gpiozero

import rclpy
from rclpy.node import Node

pin = 25

# Setup pin layout on PI
servo_pin = gpiozero.OutputDevice(pin)

# Establish Pins in software

def step(numStep, PWM_DUTY):
	#PWM_DUTY is in ms, from 1 to 2 ms
	#numSteps < 10
	if numStep >= 10:
		print("If servo issues, reduce numSteps to below 10")
	total_PWM = 20 #ms
	PWM_OFF = total_PWM - PWM_DUTY
	# Set one coil winding to high
	servo_pin.on()
	# Allow it to get there.
	sleep(PWM_DUTY/1000) # Dictates how fast stepper motor will run
	# Set coil winding to low
	servo_pin.off()
	sleep(PWM_OFF/1000) # Dictates how fast stepper motor will run


class ServoNode(Node):
	def __init__(self):
		super().__init__('servo_node')
		self.timer = self.create_timer(2.0, self.servo_control)
		self.get_logger().info('Servo node started')

	def servo_control(self):
		self.get_logger().info("right, 90")
		step(9, 2)
		sleep(1)
		self.get_logger().info("left, -90")
		step(9, 1)


def main(args=None):
	rclpy.init(args=args)
	node = ServoNode()

	try:
		rclpy.spin(node)
	finally:
		print("Shutting down...")
		node.destroy_node()
		rclpy.shutdown()


if __name__ == '__main__':
	main()
