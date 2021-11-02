from setuptools import find_packages, setup
setup(
    name='pyprediktoredgeclient',
    packages=find_packages(include=['pyprediktoredgeclient']),
    setup_requires=[
        "pythonnet>=2.5.2"
        ],

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        "": ["*.txt", "*.rst", "*.md", "*.xml", "*.xsd"],
        # And include any *.msg files found in the "hello" package, too:
        # "hello": ["*.msg"],
    },
    version='0.1.1',
    description='A Python library to talk to Prediktor APIS/EDGE',
    author='Prediktor',
    license='MIT',
)