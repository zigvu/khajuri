from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='khajuri',
      version='0.1',
      description='khajuri',
      long_description=readme(),
      classifiers=[
        'Copyright (C) ZigVu',
      ],
      packages=find_packages(),
      test_suite='nose.collector',
      tests_require=['nose', 'nose-cover3'],
      include_package_data=True,
      zip_safe=False,
      entry_points={
        'console_scripts': [
            'postprocess=tool.pp:main',
            'chia=tool.pp:main',
        ],
        },
      )
