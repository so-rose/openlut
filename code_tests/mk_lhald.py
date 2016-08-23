#!/usr/bin/env python2
from __future__ import print_function

'''
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

#Image Dims: X (0-1919), Y (0-1079), C (0-2; RGB)

import sys, os

#~ import numpy as np
#~ from PIL import Image
#~ import tifffile as tff

#~ import pylut as pl

SEP=' '
SIZE=8 #The .cube resolution is this, squared.
BIT_DEPTH=16

def imgOpen(path) :
	if path[-4:] == '.tif' or path[-4:] == 'tiff' :
		return tff.TiffFile(path).asarray()
		print("Not Supported!")
	else :
		return np.asarray(Image.open(path).convert('RGB'))

def rgbImg(img): return img.transpose(2, 0, 1) #X, Y, C --> C, X, Y
def xyImg(rgbImg): return rgbImg.transpose(1, 2, 0) #C, X, Y --> X, Y, C


def prHelp() :
	print("ml_lhald.py: Generates modified (R/B swapped) HALD files for arbitrary grading, then converts them to .cube using pylut.")
	print("\tGenerate modified HALD: ./mk_lhald.py gen <OPTIONAL: name, without extension, of png output>")
	print("\tHALD --> CUBE: ./mk_lhald.py mk <path to HALD> <OPTIONAL: name, without extension, of cube output>\n\n")
	print("Requires pylut. Install with 'pip2 install pylut'.")
	sys.exit(1)

if __name__ == "__main__" :
	if not sys.argv[1:]: prHelp()
	
	if sys.argv[1] == "gen" :
		iPath = "identity" if not sys.argv[2:] else sys.argv[2]
		os.system('convert hald:{0} {1}.png'.format(SIZE, iPath)) # -separate -swap 0,2 -combine
		
		print('Go ahead and grade the file "{}.png".'.format(iPath))
	elif sys.argv[1] == "mk" and sys.argv[1:] :
		fPath = ".converted_hald.ppm"
		lPath = "grade" if not sys.argv[3:] else sys.argv[3]
		os.system('convert -depth {2} {0} -compress none {1}'.format(sys.argv[2], fPath, BIT_DEPTH))
		
		lines = ' '.join(line.strip() for line in open(fPath, 'r').readlines()[3:]).split(' ')
		print(lines[:64*3])
		lines = ['%.6f' % (float(line)/float(2 ** BIT_DEPTH)) for line in lines] #Direct .cube output only.
		coords = [SEP.join(lines[i:i+3]) for i in range(0, len(lines)-2, 3)]
		
		identity = ' '.join([line.split(SEP)[0] for line in coords[:SIZE**2]])
		
		print(lines[:65], '\n\n', coords[:65], len(lines), len(coords))
		
		#~ with open(lPath + '.3dl', 'w') as f :
			#~ print(identity, end='\n', file=f)
			#~ print(*coords, sep='\n', file=f)
				
		print("Creating", lPath + '.cube')
		
		#~ lut = pl.LUT.FromNuke3DLFile(lPath + '.3dl')
		#~ #print(lut.ColorAtInterpolatedLatticePoint(0.00206,0.00227,0.00307))
		#~ lut.ToCubeFile(lPath + '.cube')
		
		with open(lPath + '.cube', 'w') as f :
			print("LUT_3D_SIZE", SIZE ** 2, file=f)
			print(*coords, sep='\n', file=f)
			
		os.remove(fPath)
		#~ os.remove(lPath + '.3dl')
	else :
		prHelp()
		
