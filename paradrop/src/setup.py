from setuptools import setup, find_packages

setup(
    name="paradrop",
    version="0.3.0",
    author="ParaDrop Labs",
    description="ParaDrop wireless virtualization",
    license="GPL",
    url="http://paradrop.org",
    packages=find_packages(),
    install_requires=['docker-py',
                      'ipaddress',
                      'txdbus',
                      'wget',
                      'pyyaml',
                      'pycurl',
                      'psutil',
                      'txrestapi',
                      'mock'],

    entry_points={
        'console_scripts': [
            'paradrop = paradrop:main',
            'pdconfd = paradrop:run_pdconfd'
        ]
    },

    include_package_data = True
)
