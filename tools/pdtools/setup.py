from setuptools import setup, find_packages

setup(
    name="pdtools",
    version='0.12.4',
    author="ParaDrop Labs",
    description="ParaDrop development tools",
    install_requires=[
        'appdirs~=1.4.3',
        'arrow~=0.10.0',
        'click~=6.7',
        'future~=0.16.0',
        'GitPython~=2.1.5',
        'jsonschema~=2.6.0',
        'PyYAML~=3.12',
        'requests~=2.18.1',
        'six~=1.10.0',
        'websocket-client~=0.40.0'
    ],

    packages=find_packages(),
    package_dir={'pdtools': 'pdtools'},
    package_data={'pdtools': ['schemas/*.json']},
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'pdtools = pdtools.__main__:main',
        ],
    },
)
