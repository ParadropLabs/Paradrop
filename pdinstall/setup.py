from setuptools import setup, find_packages

setup(
    name="pdinstall",
    version="0.1.0",
    author="Paradrop Labs",
    description="Paradrop installer",
    install_requires=['requests'],
    packages=find_packages(),
    zip_safe=True,
    entry_points = {
        'console_scripts': [
            'pdinstall=pdinstall.main:main'
        ]
    }
)
