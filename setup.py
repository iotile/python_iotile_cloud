from setuptools import setup
import version

setup(name='iotile_cloud',
    version=version.version,
    description='Python client for https://iotile.cloud',
    url='https://github.com/iotile/python_iotile_cloud',
    author='Arch Systems Inc.',
    author_email="info@arch-iot.com",
    license='MIT',
    packages=[
        'iotile_cloud',
        'iotile_cloud.api',
        'iotile_cloud.utils',
        'iotile_cloud.stream'
    ],
    entry_points={
        'pytest11': ['mock_cloud = iotile_cloud.utils.mock_cloud']
    },
    install_requires=[
        'future',
        'requests',
        'python-dateutil'
    ],
    keywords=["iotile", "arch", "iot", "automation"],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    zip_safe=False)
