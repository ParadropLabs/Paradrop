from setuptools import setup, find_packages

setup(
    name="pdsnappy",
    version="0.1",
    author="Paradrop Labs",
    description="Paradrop wireless virtualization",
    install_requires=['twisted'],
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'pdsnappy=paradrop:main',
        ],
    },
)
