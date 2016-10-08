from setuptools import setup

setup(name='pystrato',
      version='0.2.0',
      description='Python client for strato.arch-iot.com',
      url='https://github.com/iotile/strato_python_api',
      author='David Karchmer',
      author_email='david@arch-iot.com',
      license='MIT',
      packages=['pystrato'],
      install_requires=[
        'requests',
      ],
      zip_safe=False)