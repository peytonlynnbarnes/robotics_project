import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

from smbus2 import SMBus
import time

import math

# MPU6050 Registers
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# Initialize I2C bus (1 for Raspberry Pi)
bus = SMBus(1)

# Wake up MPU6050 (it starts in sleep mode)
bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
def mpu_init():
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

def read_word_2c(addr):
    high = bus.read_byte_data(MPU6050_ADDR, addr)
    low = bus.read_byte_data(MPU6050_ADDR, addr + 1)
    value = (high << 8) + low

    if value >= 0x8000:
        return -((65535 - value) + 1)
    else:
        return value

def get_accel():
    x = read_word_2c(ACCEL_XOUT_H)
    y = read_word_2c(ACCEL_XOUT_H + 2)
    z = read_word_2c(ACCEL_XOUT_H + 4)

    # Convert to g (default sensitivity = ±2g)
    x /= 16384.0
    y /= 16384.0
    z /= 16384.0

    return x, y, z

def get_gyro():
    x = read_word_2c(GYRO_XOUT_H)
    y = read_word_2c(GYRO_XOUT_H + 2)
    z = read_word_2c(GYRO_XOUT_H + 4)

    # Convert to degrees/sec (default sensitivity = ±250°/s)
    x /= 131.0
    y /= 131.0
    z /= 131.0

    return x, y, z

#try:
 #   while True:
  #      accel = get_accel()
   #     gyro = get_gyro()

   #     print(f"Accel (g): X={accel[0]:.2f}, Y={accel[1]:.2f}, Z={accel[2]:.2f}")
   #     print(f"Gyro (°/s): X={gyro[0]:.2f}, Y={gyro[1]:.2f}, Z={gyro[2]:.2f}")
   #     print("-" * 40)

    #    time.sleep(0.5)

#except KeyboardInterrupt:
 #   print("Exiting...")

class IMUPublisher(Node):
    def __init__(self):
        super().__init__('mpu6050_node')

        self.publisher_ = self.create_publisher(Imu, '/imu/data', 10)
        self.timer = self.create_timer(0.02, self.publish_imu)  # 50 Hz

        mpu_init()
        self.get_logger().info("MPU6050 publisher started")

    def publish_imu(self):
        msg = Imu()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"

        ax, ay, az = get_accel()
        gx, gy, gz = get_gyro()

        # Convert to ROS units
        msg.linear_acceleration.x = ax * 9.80665
        msg.linear_acceleration.y = ay * 9.80665
        msg.linear_acceleration.z = az * 9.80665

        msg.angular_velocity.x = math.radians(gx)
        msg.angular_velocity.y = math.radians(gy)
        msg.angular_velocity.z = math.radians(gz)

        # No orientation provided
        msg.orientation_covariance[0] = -1.0

        self.publisher_.publish(msg)

# =========================
# MAIN
# =========================
def main(args=None):
    rclpy.init(args=args)
    node = IMUPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()