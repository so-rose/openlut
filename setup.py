#!/usr/bin/env python3

import sys, os
import os.path as path

#~ from sysconfig import get_python_version, get_path

from setuptools import setup
from setuptools import Extension
from setuptools import find_packages

#Weirdly long way to get to the actual header files we need to include.
#~ pyPath = path.join(path.abspath(get_path('include') + os.sep + '..'), 'site/python{}'.format(get_python_version()))

#Better - Mac & Linux only.
#~ pyPath = '/usr/local/include/python{}'.format(get_python_version())'

cpp_args = ['-fopenmp', '-std=gnu++14']
link_args = ['-fopenmp']

olOpt = Extension(	'openlut.lib.olOpt',
					sources = ['openlut/lib/olOpt.cpp'],
					#~ include_dirs=[pyPath], #Include from the the python3 source code.
					language = 'c++',
					extra_compile_args = cpp_args,
					extra_link_args = cpp_args
		)

setup(	name = 'openlut',
		version = '0.1.4',
		description = 'OpenLUT is a practical color management library.',
		author = 'Sofus Rose',
		author_email = 'sofus@sofusrose.com',
		url = 'https://www.github.com/so-rose/openlut',
		
		packages = find_packages(exclude=['src']),
		
		ext_modules = [olOpt],

		license = 'MIT Licence',
		
		keywords = 'color image images processing',
		
		install_requires = ['numpy', 'wand', 'scipy', 'pygame','PyOpenGL', 'setuptools'],
		
		classifiers = [
			'Development Status :: 3 - Alpha',
			
			'License :: OSI Approved :: MIT License',
			
			'Programming Language :: Python :: 3'
		]
)
