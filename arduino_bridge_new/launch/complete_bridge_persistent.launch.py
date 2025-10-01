from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    print("TurtleBot Complete Bridge with Persistent Device Names")
    print("Arduino: /dev/ttyARDUINO")
 
    arduino_bridge = Node(
        package='arduino_bridge_new',
        executable='arduino_bridge',
        name='arduino_bridge',
        parameters=[{
            'serial_port': LaunchConfiguration('serial_port'),
            'baud_rate': LaunchConfiguration('baud_rate'),
            'serial_timeout': 1.0,
            'reconnect_attempts': 5,
            'wheel_radius': LaunchConfiguration('wheel_radius'),
            'wheel_separation': LaunchConfiguration('wheel_separation'),
        }],
        output='screen'
    )

    # Wheel velocity publisher
    wheel_velocity_publisher = Node(
        package='arduino_bridge_new',
        executable='wheel_velocity_publisher',
        name='wheel_velocity_publisher',
        parameters=[{
            'wheel_radius': LaunchConfiguration('wheel_radius'),
            'wheel_separation': LaunchConfiguration('wheel_separation'),
        }],
        output='screen'
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyARDUINO',
            description='Persistent serial port for Arduino'
        ),
        DeclareLaunchArgument(
            'baud_rate',
            default_value='115200',
            description='Baud rate for serial communication'
        ),
        DeclareLaunchArgument(
            'wheel_radius',
            default_value='0.033',
            description='Wheel Radius'
        ),
        DeclareLaunchArgument(
            'wheel_separation',
            default_value='0.175',
            description='Wheel Separation'
        ),
        wheel_velocity_publisher,
        arduino_bridge
    ])
