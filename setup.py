from setuptools import setup

package_name = 'nav2_fault_inject'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='darshmenon',
    maintainer_email='darshmenon02@gmail.com',
    description='Pause nodes of a running ROS 2 stack to test that it notices and recovers.',
    license='Apache-2.0',
    entry_points={'console_scripts': ['nav2_fault_inject = nav2_fault_inject.cli:main']},
)
