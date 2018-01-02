from setuptools import setup, find_packages

setup(
    name="paradrop",
    version='0.10.1',
    author="ParaDrop Labs",
    description="ParaDrop wireless virtualization",
    license="GPL",
    url="http://paradrop.org",
    packages=find_packages(),
    install_requires=[
        'attrs',
        'autobahn>=0.15.0',
        'bcrypt>=2.0.0',
        'colorama>=0.3.3',
        'docker==2.5.1',
        'enum34',
        'idna>=2.0',
        'ipaddress',
        'jsonpatch==1.15',
        'klein==16.12.0',
        'netifaces==0.10.4',
        'psutil',
        'pycurl',
        'PyJWT>=1.5.3',
        'pyyaml',
        'requests==2.15.1', # Fix requests version until we can get idna>=2.5.
        'service_identity>=16.0.0',
        'smokesignal>=0.7.0',
        'Twisted==16.2.0',
        'txdbus',
        'txmsgpackrpc>=1.1',
        'txsockjs==1.2.2',
        'wget'
    ],

    entry_points={
        'console_scripts': [
            'paradrop = paradrop:main',
            'pdconfd = paradrop:run_pdconfd'
        ]
    },

    include_package_data = True
)
