#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='pyetherpadlite',
    version='0.2',
    description='Python bindings for Etherpad-Lite\'s HTTP API. (https://github.com/guyzmo/etherpad-lite)',
    author='devjones, guyzmo',
    url='https://github.com/guyzmo/PyEtherpadLite',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires = [
        "socketIO-client"
    ],
    entry_points="""
        # -*- Entry points: -*-
        [console_scripts]
        pyepad = py_etherpad:cli
        """,



)

