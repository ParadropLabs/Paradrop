from setuptools import setup, find_packages

setup(
    name="paradrop",
    version="0.2.0",
    author="Paradrop Labs",
    description="Paradrop wireless virtualization",
    install_requires=['docker-py',
                      'ipaddress',
                      'txdbus',
                      'wget',
                      'pyyaml',
                      'psutil',
                      'pdtools>=0.2.00',
                      'mock'],
    packages=find_packages(),

    entry_points={
        'console_scripts': [
            'paradrop=paradrop:main',
            'pdconfd=paradrop:run_pdconfd'
        ],
    },

    include_package_data = True
)
