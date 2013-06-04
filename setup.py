#!/usr/bin/env python

from setuptools import setup
import glob

setup(name='patchwork',
    version='0.4',
    description='Multihost actions toolbox',
    author='Vitaly Kuznetsov',
    author_email='vitty@redhat.com',
    url='https://github.com/RedHatQE/python-patchwork',
    license="GPLv3+",
    packages=[
        'patchwork'
        ],
    classifiers=[
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Operating System :: POSIX',
            'Intended Audience :: Developers',
            'Development Status :: 4 - Beta'
    ]
)
