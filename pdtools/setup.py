'''
I know this is confusing naming, this is a temp fix
'''

from setuptools import setup, find_packages

setup(
    name="pdtools",
    version="0.1.40",
    author="Paradrop Labs",
    description="Paradrop deployment and build tools",
    install_requires=[
        'docopt>=0.6.2',
        'requests>=2.7.0',
        'twisted>=14.2',
        'bcrypt>=2.0.0',
        'service-identity>=14.0.0',
        'colorama>=0.3.3',
        'pyyaml>=3.11'
    ],

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'paradrop=pdtools.main:main',
        ],
    },
)
