from setuptools import find_packages, setup

package_name = 'arduino_bridge_new'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/complete_bridge_persistent.launch.py',
            'launch/arduino_bridge_persistent.launch.py',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='aditya-pachauri',
    maintainer_email='aditya-pachauri@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'arduino_bridge = arduino_bridge_new.arduino_bridge:main',
            'wheel_velocity_publisher = arduino_bridge_new.wheel_velocity_publisher:main',
        ],
    },
)
