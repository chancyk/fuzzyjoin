#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'Click>=7.0,<8.0',
    'pylev>=1.3.0,<1.4.0'
]

test_requirements = [
]

setup(
    name='fuzzyjoin',
    version='0.2.1',
    description="Join two tables by a fuzzy comparison of text columns.",
    long_description=readme,
    author="Chancy Kennedy",
    author_email='kennedychancy+fuzzyjoin@gmail.com',
    url='https://github.com/chancyk/fuzzyjoin',
    packages=[
        'fuzzyjoin',
    ],
    package_dir={'fuzzyjoin':
                 'fuzzyjoin'},
    entry_points={
        'console_scripts': [
            'fuzzyjoin=fuzzyjoin.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='fuzzyjoin',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
