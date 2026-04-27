from setuptools import find_packages, setup

package_name = 'lowlevel'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/lowlevel.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ROS User',
    maintainer_email='ros@example.com',
    description='Low-level hardware control package for robot motors and IMU',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'servo_node = lowlevel.gpiozero_servo:main',
            'stepper_left_node = lowlevel.gpiozero_stepper_motor_1:main',
            'stepper_right_node = lowlevel.gpiozero_stepper_motor_2:main',
            'imu_node = lowlevel.IMU_test:main',
        ],
    },
)
