from setuptools import setup, find_packages

setup(
    name="hello-world-python2",
    version="0.1.0",
    author="ParaDrop Lab",
    license="Apache 2",
    packages=find_packages(),
    install_requires=[
        'flask>=0.12'
    ],

    entry_points={
        'console_scripts': [
            'helloworld = helloworld.server:main'
        ]
    },

    include_package_data = True
)
