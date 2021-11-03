from setuptools import find_packages, setup
setup(
    name='pyprediktoredgeclient',
    packages=find_packages(include=['pyprediktoredgeclient']),
    setup_requires=[
        "pythonnet>=2.5.2"
        ],

    include_package_data=True,
    version='0.1.5',
    description='A Python library to talk to Prediktor APIS/EDGE',
    author='Prediktor',
    license='MIT',
)