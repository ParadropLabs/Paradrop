from setuptools import setup, find_packages

with open("../../README.md", "r") as source:
    long_description = source.read()

setup(
    name="paradrop",
    version='0.13.3a8',
    description="Paradrop Edge Computing Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://paradrop.org",

    project_urls = {
        "Documentation": "https://paradrop.readthedocs.io/en/latest/",
        "Homepage": "https://paradrop.org",
        "Source": "https://github.com/ParadropLabs/Paradrop",
    },

    packages=find_packages(),

    install_requires=[
        'attrs==18.2.0',
        'autobahn==18.8.1',
        'bcrypt==3.1.4',
        'colorama==0.3.9',
        'configparser==3.7.1',
        'docker==2.5.1',
        'enum34',
        'functools32==3.2.3.post2; python_version < "3.2"',
        'future==0.16.0',
        'ipaddress>=1.0.16',
        'jsonpatch==1.15',
        'klein==16.12.0',
        'netifaces==0.10.4',
        'psutil==5.6.2',
        'pulsectl==17.12.2',
        'pycurl',
        'PyJWT==1.6.4',
        'PyYAML==5.1',
        'requests==2.21.0',
        'ruamel.ordereddict==0.4.13; python_version < "3.1"',
        'ruamel.yaml==0.15.60',
        'service_identity==17.0.0',
        'six>=1.10.0',
        'smokesignal==0.7.0',
        'Twisted==16.2.0',
        'wget==3.2'
    ],

    python_requires=">=2.7",

    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],

    maintainer="Lance Hartung",
    maintainer_email="lance@paradrop.io",

    include_package_data=True,
    package_data={
        "paradrop": ["static/*"]
    },

    entry_points={
        'console_scripts': [
            'paradrop = paradrop:main',
            'pdconfd = paradrop:run_pdconfd'
        ]
    },
)
