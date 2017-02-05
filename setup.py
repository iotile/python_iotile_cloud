from setuptools import setup
import version

setup(name='iotile_cloud',
    version=version.version,
    description='Python client for https://iotile.cloud',
    url='https://github.com/iotile/python_iotile_cloud',
    author='David Karchmer',
    author_email='david@arch-iot.com',
    license='MIT',
    packages=[
        'iotile_cloud',
        'iotile_cloud.api',
        'iotile_cloud.stream'
    ],
    install_requires=[
        'requests'
    ],
    keywords=["iotile", "arch", "embedded", "hardware"],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    zip_safe=False)
