from setuptools import setup, find_packages

VERSION = '0.1.1'

setup(
    name='python-params',
    version=VERSION,
    description='Python files parametrization library',
    author='shelfwise.ai',
    author_email='krzysztof.kolasinski@shelfwise.ai',
    url='https://github.com/fornaxai/pyparams',
    packages=find_packages(exclude=["tests", "resources"]),
    install_requires=[
        "pytest>=3.3.0",
        "astor==0.6.2",
        "natsort==5.3.3",
        "pyyaml==5.1",
        "dataclasses==0.6"
    ],
    scripts=[
        "scripts/pyparams"
    ],
    include_package_data=True
)
