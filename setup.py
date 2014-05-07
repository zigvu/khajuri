from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='VideoPipeline',
      version='0.1',
      description='VideoPipeline',
      long_description=readme(),
      classifiers=[
        'Copyright (C) ZigVu',
      ],
      packages=['Controller', 'tests', 'plugins', 'Swf']
      test_suite='nose.collector',
      tests_require=['nose', 'nose-cover3'],
      include_package_data=True,
      zip_safe=False)
