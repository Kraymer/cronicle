#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

from setuptools import setup


def coerce_file(fn):
    """Coerce file content to something useful for setuptools.setup(), turn :
       .py into mock object by extracting __special__ attributes values
       .md into rst text. Remove images with "[nopypi" alt text and emojis
       :url: https://github.com/Kraymer/setupgoon
    """
    import ast
    import os
    import re
    import subprocess
    import tempfile
    import time  # noqa
    text = open(os.path.join(os.path.dirname(__file__), fn)).read()
    if fn.endswith('.py'):  # extract version, docstring etc out of python file
        mock = type('mock', (object,), {})()
        for attr in ('version', 'author', 'author_email', 'license', 'url'):
            regex = r'^__%s__\s*=\s*[\'"]([^\'"]*)[\'"]$' % attr
            m = re.search(regex, text, re.MULTILINE)
            setattr(mock, attr, m.group(1) if m else None)
        mock.docstring = ast.get_docstring(ast.parse(text))
        if mock.version.endswith('dev'):
            mock.version += str(int(time.time()))
        return mock
    if fn.endswith('md'):  # convert md to rest on pypi package upload
        text = '\n'.join([l for l in text.split('\n') if '[nopypi' not in l])
        text = re.sub(r':\S+:', '', text)  # no emojis
        with tempfile.NamedTemporaryFile(mode='w+') as tmp:
            tmp.write(text)
            tmp.flush()
            try:
                text, stderr = subprocess.Popen(['pandoc', '-t', 'rst', tmp.name],
                                                stdout=subprocess.PIPE).communicate()
            except:
                pass
    try:
        return text.decode('utf-8')
    except AttributeError:
        return text


setup(name='cronicle',
      version=coerce_file('cronicle/__init__.py').version,
      description=coerce_file('cronicle/__init__.py').docstring,
      long_description=coerce_file('README.md'),
      author='Fabrice Laporte',
      author_email='kraymer@gmail.com',
      url='https://github.com/KraYmer/cronicle',
      license='MIT',
      platforms='ALL',
      packages=['cronicle', ],
      entry_points={
          'console_scripts': [
              'cronicle = cronicle:cronicle_cli',
          ],
      },
      install_requires=coerce_file('requirements.txt').split('\n'),
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Environment :: Console',
          'Topic :: System :: Filesystems',
      ],
      keywords="cron rotate backup",
      )
