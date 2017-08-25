from setuptools import setup, find_packages

setup(
    name="pdlog",
    version="0.1.0",
    author="ParaDrop Lab",
    license="Apache 2",
    packages=find_packages(),
    install_requires=[
    ],

    entry_points={
        'console_scripts': [
            'pdlog = pdlog:main'
        ]
    },

    include_package_data = True
)
