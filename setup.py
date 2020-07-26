from setuptools import setup, find_namespace_packages

setup(
    name='info_epd_deps',
    description='e-Paper Info Dependencies',
    version='0.1.0',
    package_dir={'': 'lib'},
    packages=find_namespace_packages(where="lib"))
