import os, sys

import unittest as ut

from os import path

sys.path.append(0, path.abspath('..'))

from openlut import *

def verifyLUT(lut, title, size, iRange) :
	assertEqual(lut.title, title)
	assertEqual(lut.size, size)
	assertEqual(lut.range, iRange)
	assertEqual(lut.dims, 1)
	assertEqual(lut.ID, np.linspace(iRange[0], iRange[1], size))
	
	assertEqual(str(lut.array), 'float32')

class testLUT(ut.TestCase) :
	def test_init(self) :
		lut = LUT(title="test", size=4096, iRange=(-0.125, 1.125))
		
		verifyLUT(lut, 'test', 4096, (-0.125, 1.125))
		
		#~ assertEqual(lut.title, 'test')
		#~ assertEqual(lut.size, 4096)
		#~ assertEqual(lut.range, (-0.125, 1.125))
		#~ assertEqual(lut.dims, 1)
		#~ assertEqual(lut.ID, np.linspace(-0.125, 1.125, 4096))
		#~ assertEqual(lut.array, np.linspace(-0.125, 1.125, 4096))
		
	def test_func(self) :
		lut = LUT.lutFunc(gamma.sRGB, title='test', size=4096, iRange=(-0.125, 1.125))
		
		verifyLUT(lut, 'test', 4096, (-0.125, 1.125))
