from setuptools import setup, find_packages

setup(
    name="paradrop",
    version='0.12.1',
    author="ParaDrop Labs",
    description="ParaDrop wireless virtualization",
    license="GPL",
    url="http://paradrop.org",
    packages=find_packages(),
    install_requires=[
        'attrs==18.2.0',
        'autobahn==18.8.1',
        'bcrypt==3.1.4',
        'colorama==0.3.9',
        'docker==2.5.1',
        'enum34',
        'idna>=2.0',
        'ipaddress>=1.0.16',
        'jsonpatch==1.15',
        'klein==16.12.0',
        'netifaces==0.10.4',
        'psutil==5.4.7',
        'pulsectl==17.12.2',
        'pycurl',
        'PyJWT==1.6.4',
        'PyYAML==3.13',
        'requests==2.15.1', # Fix requests version until we can get idna>=2.5.
        'ruamel.ordereddict==0.4.13',
        'ruamel.yaml==0.15.60',
        'service_identity==17.0.0',
        'six>=1.10.0',
        'smokesignal==0.7.0',
        'Twisted==16.2.0',
        'txdbus==1.1.0',
        'txmsgpackrpc==1.2',
        'txsockjs==1.2.2',
        'wget==3.2'
    ],

    entry_points={
        'console_scripts': [
            'paradrop = paradrop:main',
            'pdconfd = paradrop:run_pdconfd'
        ]
    },

    include_package_data = True
)
