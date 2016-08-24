from setuptools import setup, find_packages
from delta import __version__

setup(name='delta',
      version=__version__,
      description='Iterative diffing for CSV',
      url='https://github.com/cityofphiladelphia/delta',
      author='City of Philadelphia',
      author_email='robert.martin@phila.gov',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'Click',
      ],
      entry_points='''
          [console_scripts]
          delta=delta.main:main
      ''',
      zip_safe=False)
