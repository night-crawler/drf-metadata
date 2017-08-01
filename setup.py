from setuptools import setup, find_packages

from drf_metadata import __version__

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='drf-metadata',
    version=__version__,
    packages=find_packages(),
    url='https://github.com/night-crawler/drf-metadata',
    license='MIT',
    author='night-crawler',
    author_email='lilo.panic@gmail.com',
    description='Metadata generator for Django Rest Framework',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License',
    ],
    requires=['django', 'djangorestframework']
)
