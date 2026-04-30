#handsontec.com/dataspecs/motor_fan/MGR996R.pdf
from time import sleep
import RPi.GPIO as GPIO
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

pin = 25

# Setup pin layout on PI
#servo = Servo(pin)
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
		self.timer = self.create_timer(12.0, self.servo_control)
		self.get_logger().info('Servo node started')

		self.servo_side = "left"

		self.subscription_status = self.create_subscription(
			String,
			'/latch_status',
			self.listener_callback,
			10
		)
		#self.subscription_person = self.create_subscription(
		#	String,
		#	'',
		#	self.listener_callback_status,
		#	10
		#)
	def listener_callback(self, msg):
		self.get_logger().info("Servo received callback msg")
		#self.get_logger().info(msg)
		if msg.data == "opened":
			self.get_logger().info("Servo active")
			self.get_logger().info("right, 90")
			step(9, 2.2)
			sleep(5)
			

		elif msg.data == "closed":
			self.get_logger().info("left, -90")
			step(9, 1.1)
			sleep(5)


	def listener_callback_status(self, msg):
		if name == "Louis":
			self.servo_side = "right"
		else:
			self.servo_side = "left"
	def servo_control(self):
		self.get_logger().info("right, 90")
		step(9, 2.2)
		sleep(1)
		self.get_logger().info("left, -90")
		step(9, 1.1)
		sleep(1)


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
