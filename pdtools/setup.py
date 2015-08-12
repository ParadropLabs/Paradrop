'''
I know this is confusing naming, this is a temp fix
'''

from setuptools import setup, find_packages

setup(
    name="pdtools",
    version="0.1.51",
    author="Paradrop Labs",
    description="Paradrop deployment and build tools",
    install_requires=[
        'bcrypt>=2.0.0',
        'cffi>=1.1.2',
        'colorama>=0.3.3',
        'docopt>=0.6.2',
        'enum>=0.4.4',
        'enum34>=1.0.0',
        'pyyaml>=3.11',
        'requests>=2.7.0',
        'service-identity>=14.0.0',
        'twisted>=14.2',
        'pypubsub>=3.3.0'
    ],

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'paradrop=pdtools.main:main',
        ],
    },
)
