#!/usr/bin/env python
import os
from codecs import open
from setuptools import setup

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_readme():
    with open(os.path.join(THIS_DIR, 'README.md'), encoding='utf-8') as fobj:
        out = fobj.read()

    try:
        import m2r
    except ImportError:
        # must be running on fellow dev computer - no need to do fancy
        # markdown conversion
        return out
    else:
        # Probably an sqlalchemy-fsm dev environment.
        #   Might be publishing to pypi.
        #   Better to perform the conversion
        return m2r.convert(out)


setup(
    name='cfalchemy',
    packages=['cfalchemy'],
    py_modules=['cfalchemy'],
    description='Objective mapper for AWS stacks',
    long_description=get_readme(),
    author='Ilja Orlovs',
    author_email='ilja@wise.fish',
    license='MIT',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    keywords='aws amazon cloudformation',
    version='2.0.6',
    url='https://github.com/VRGhost/cfalchemy',
    install_requires=[
        'boto3>=1',
        'six>=1.10.0',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
