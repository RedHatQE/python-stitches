#!/usr/bin/env python

""" setup.py """

from setuptools import setup

setup(name='stitches',
    version='0.18',
    description='Multihost actions toolbox',
    author='Vitaly Kuznetsov',
    author_email='vitty@redhat.com',
    url='https://github.com/RedHatQE/python-stitches',
    license="GPLv3+",
    install_requires=['paramiko >= 1.10', 'nose', 'PyYAML', 'plumbum', 'rpyc'],
    packages=[
        'stitches'
        ],
    classifiers=[
            'License :: OSI Approved :: GNU General Public\
 License v3 or later (GPLv3+)',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Operating System :: POSIX',
            'Intended Audience :: Developers',
            'Development Status :: 4 - Beta'
    ]
)
