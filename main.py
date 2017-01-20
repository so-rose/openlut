#!/usr/bin/env python3.5

'''
openlut: A package for managing and applying 1D and 3D LUTs.

Color Management: openlut deals with the raw RGB values, does its work, then puts out images with correct raw RGB values - a no-op.

Dependencies:
	-numpy: Like, everything.
	-wand: Saving/loading images.
	-PyOpenGL - For image viewer and other future graphics processing.
	-pygame - For the physical display in the viewer.
	-scipy - OPTIONAL: For spline interpolation.
	
Easily get all deps: sudo pip3 install numpy wand scipy PyOpenGL pygame

*Make sure you get the Python 3.X version of these packages!!!



LICENCE:

The MIT License (MIT)

Copyright (c) 2016 Sofus Rose

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import sys

#~ from lib.files import Log #For Development

if __name__ == "__main__" :
	if not sys.argv[1:]: print('Use -t to test!'); exit()

	if sys.argv[1] == '-t' :
		import tests.suite
		tests.suite.runTest('img_test', 'testpath')
