from setuptools import setup, find_packages

with open("README.md", "r") as source:
    long_description = source.read()

setup(
    name="pdtools",
    version='0.13.2',
    description="Paradrop Developer Tools",
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
        'appdirs~=1.4.3',
        'arrow~=0.10.0',
        'click~=6.7',
        'future~=0.16.0',
        'GitPython~=2.1.5',
        'jsonschema~=2.6.0',
        'PyYAML~=5.1',
        'requests>=2.21.0',
        'six~=1.10.0',
        'websocket-client~=0.40.0'
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

    package_dir={'pdtools': 'pdtools'},
    package_data={'pdtools': ['schemas/*.json']},
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'pdtools = pdtools.__main__:main',
        ],
    },
)
