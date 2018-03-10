from setuptools import setup

setup(name='sds011',
      version='0.1',
      description='Library for the SDS011 dust sensor',
      url='http://github.com/xvzf/SDS011-python',
      author='Matthias Riegler',
      author_email='matthias@xvzf.tech',
      license='GPLv3',
      packages=['sds011'],
      install_requires=[
          'pyserial',
      ],
      zip_safe=False)