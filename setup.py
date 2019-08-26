#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import shutil
import sys
from io import open

from setuptools import find_packages, setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('caravaggio_rest_api')


if sys.argv[-1] == 'publish':
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    shutil.rmtree('dist')
    shutil.rmtree('build')
    shutil.rmtree('django-caravaggio-rest-api.egg-info')
    sys.exit()


setup(
    name='django-caravaggio-rest-api',
    version=version,
    url='http://www.preseries.com',
    license='MIT',
    description='A Django REST API for BigData Projects.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Javier Alperte',
    author_email='alperte@preseries.com',  # SEE NOTE BELOW (*)
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=[
        'wheel>=0.30.0',
        'django>=2',
        'django-cassandra-engine==1.5.4.preseries-1',
        # 'djangorestframework>=3.7,<3.10',
        'djangorestframework-queryfields>=1.0.0',
        'django-rest-swagger>=2.2.0',
        'rest-framework-cache>=0.1',
        'django-redis>=4.10.0',
        'markdown>=2.6.11',
        'gdal==2.3.2',
        'geopy>=1.17.0',
        'drf-haystack>=1.8.5',
        'pysolr>=3.7.0',
        'solrq>=1.1.1',
        'fuzzywuzzy>=0.17'],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ],
    dependency_links=[
        "https://github.com/preseries/django-cassandra-engine/tarball/"
        "1.5.4-preseries-1#egg=django-cassandra-engine-1.5.4.preseries-1",
    ],
)

# (*) Please direct queries to the discussion group, rather than to me directly
#     Doing so helps ensure your question is helpful to other users.
#     Queries directly to my email are likely to receive a canned response.
#
#     Many thanks for your understanding.
