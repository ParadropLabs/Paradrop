from setuptools import setup, find_packages

setup(
    name="paradrop",
    version="0.1",
    author="Paradrop Labs",
    description="Paradrop wireless virtualization",
    install_requires=['twisted', 'wget'],
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'paradrop=paradrop:main',
        ],
    },
)
