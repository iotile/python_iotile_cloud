from setuptools import setup

setup(name='iotile_cloud',
      version='0.4.0',
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
        'requests',
      ],
      zip_safe=False)