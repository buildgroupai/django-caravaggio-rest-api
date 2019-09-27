#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import shutil
import sys
from io import open

from setuptools import setup
import traceback

extra_params = {}
setup_requires = [
    'sphinx==2.2.0',
    'sphinxcontrib-inlinesyntaxhighlight==0.2']

try:
    from pip._internal import main
    main(['install'] + setup_requires)
    setup_requires = []
except Exception:
    # Going to use easy_install for
    traceback.print_exc()


def read(f):
    return open(f, 'r', encoding='utf-8').read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('src/caravaggio_rest_api')


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

from sphinx.setup_command import BuildDoc

cmd_class = {
    'docs': BuildDoc,
}

setup(
    version=version,
    cmdclass=cmd_class,
    command_options={
        'docs': {
            'project': ('setup.py', 'caravaggio-rest-api'),
            'version': ('setup.py', version),
            'release': ('setup.py', version),
            'source_dir': ('setup.py', 'docs'),
            'build_dir': ('setup.py', '_build_docs')}},
    setup_requires=setup_requires,
    setup_cfg=True
)

# (*) Please direct queries to the discussion group, rather than to me directly
#     Doing so helps ensure your question is helpful to other users.
#     Queries directly to my email are likely to receive a canned response.
#
#     Many thanks for your understanding.
