'''
I know this is confusing naming, this is a temp fix
'''

from setuptools import setup, find_packages

setup(
    name="paradrop",
    version="0.1.15",
    author="Paradrop Labs",
    description="Paradrop deployment and build tools",
    install_requires=['docopt', 'requests', 'twisted', 'bcrypt'],
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'paradrop=pdtools.main:main',
        ],
    },
)
