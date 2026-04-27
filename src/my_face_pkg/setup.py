from setuptools import setup

package_name = 'my_face_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            'facial_recognition = my_face_pkg.facial_recognition_node:main',
        ],
    },
)