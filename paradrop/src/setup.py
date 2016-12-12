from setuptools import setup, find_packages

setup(
    name="paradrop",
    version="0.3.0",
    author="ParaDrop Labs",
    description="ParaDrop wireless virtualization",
    license="GPL",
    url="http://paradrop.org",
    packages=find_packages(),
    install_requires=[
        'autobahn>=0.15.0',
        'bcrypt>=2.0.0',
        'colorama>=0.3.3',
        'requests>=2.7.0',
        'smokesignal>=0.7.0',
        'service_identity>=16.0.0',
        'attrs',
        'enum34',
        'docker-py',
        'ipaddress',
        'txdbus',
        'wget',
        'pyyaml',
        'pycurl',
        'psutil',
        'txrestapi',
        'txmsgpackrpc>=1.1'
    ],

    entry_points={
        'console_scripts': [
            'paradrop = paradrop:main',
            'pdconfd = paradrop:run_pdconfd'
        ]
    },

    include_package_data = True
)
