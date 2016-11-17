from setuptools import setup

setup(name='pystrato',
      version='0.3.0',
      description='Python client for https://iotile.cloud',
      url='https://github.com/iotile/strato_python_api',
      author='David Karchmer',
      author_email='david@arch-iot.com',
      license='MIT',
      packages=['pystrato'],
      install_requires=[
        'requests',
      ],
      zip_safe=False)