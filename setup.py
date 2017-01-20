#!/usr/bin/env python3

from setuptools import setup
from setuptools import Extension
from setuptools import find_packages

cpp_args = ['-fopenmp', '-std=gnu++14']
link_args = ['-fopenmp']

olOpt = Extension(	'openlut.lib.olOpt',
					sources = ['openlut/lib/olOpt.cpp'],
					language = 'c++',
					extra_compile_args = cpp_args,
					extra_link_args = cpp_args
		)

setup(	name = 'openlut',
		version = '0.1.1',
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
