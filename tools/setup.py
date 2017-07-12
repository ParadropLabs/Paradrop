from setuptools import setup, find_packages

setup(
    name="pdtools",
    version="0.7.1",
    author="Paradrop Labs",
    description="Paradrop deployment and build tools",
    install_requires=[
        'click>=6.7',
        'future>=0.16.0',
        'PyYAML>=3.12',
        'requests>=2.18.1'
    ],

    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'pdtools=pdtools.main:main',
        ],
    },
)
