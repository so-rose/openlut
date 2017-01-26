import os, sys

#Script must be called from openlut root.

sys.path.insert(0, '.')

from openlut import *

def runTest(inPath, path) :
	print('Open openlut.py and scroll down to the end to see the code that\'s working!')
	#Open any format image. Try it with exr/dpx/anything!
	img = ColMap.open(inPath + '/rock.exr') #Opens a test image 'test.exr', creating a ColMap object, automatically using the best image backend available to load the image at the correct bit depth.

	'''
	gamma has gamma functions like gamma.sRGB, called by value like gamma.sRGB(val). All take one argument, the value (x), and returns the transformed value. Color doesn't matter for gamma.
	gamut has matrices, in 3x3 numpy array form. All are relative to ACES, with direction aptly named. So, gamut.XYZ is a matrix from ACES --> XYZ, while gamut.XYZinv goes from XYZ --> ACES. All use/are converted to the D65 illuminant, for consistency sake.
	'''

	#gamma Functions: sRGB --> Linear.
	gFunc = Func(gamma.sRGBinv) #A Func Transform object using the sRGB-->Linear gamma formula. Apply to ColMaps!
	gFuncManualsRGB = Func(lambda val: ((val + 0.055) / 1.055) ** 2.4 if val > 0.04045 else val / 12.92) #It's generic - specify any gamma function, even inline with a lambda!

	#LUT from Function: sRGB --> Linear
	oLut = LUT.lutFunc(gamma.sRGBinv) #A LUT Transform object, created from a gamma function. Size is 16384 by default. LUTs are faster!
	oLut.save(path + '/sRGB-->Lin.cube') #Saves the LUT to a format inferred from the extension. cube only for now!

	#Opening LUTs from .cube files.
	lut = LUT.open(path + '/sRGB-->Lin.cube') #Opens the lut we just made into a different LUT object.
	lut.resized(17).save(path + '/sRGB-->Lin_tiny.cube') #Resizes the LUT, then saves it again to a much smaller file!

	#Matrix Transformations
	simpleMat = ColMat(gamut.sRGBinv) #A Matrix Transform (ColMat) object, created from a color transform matrix for gamut transformations! This one is sRGB --> ACES.
	mat = ColMat(gamut.sRGBinv, gamut.XYZ, gamut.XYZinv, gamut.aRGB) * gamut.aRGBinv
	#Indeed, specify many matrices which auto-multiply into a single one! You can also combine them after, with simple multiplication.

	#Applying and saving.
	img.apply(gFunc).save(path + '/openlut_gammafunc.png') #save saves an image using the appropriate image backend, based on the extension.
	img.apply(lut).save(path + '/openlut_lut-lin-16384.png') #apply applies any color transformation object that inherits from Transform - LUT, Func, ColMat, etc., or make your own! It's easy ;) .
	img.apply(lut.resized(17)).save(path + '/openlut_lut-lin-17.png') #Why so small? Because spline interpolation automatically turns on. It's identical to the larger LUT!
	img.apply(mat).save(path + '/openlut_mat.png') #Applies the gamut transformation.

	#As a proof of concept, here's a long list of transformations that should, in sum, do nothing :) :

	img.apply(lut).apply(LUT.lutFunc(gamma.sRGB)).apply(mat).apply(~mat).save('testpath/openlut_noop.png') #~mat is the inverse of mat. Easily undo the gamut operation!

	#Format Test: All output images are in Linear ACES.
	tImg = img.apply(mat)
	tImg.save(path + '/output.exr')
	tImg.save(path + '/output.dpx')
	tImg.save(path + '/output.png')
	tImg.save(path + '/output.jpg')
	tImg.save(path + '/output.tif') #All sorts of formats work! Bit depth is 16, unless you say something else.

	#Compression is impossible right now - wand is being difficult.
	#Keep in mind, values are clipped from 0 to 1 when done. Scary transforms can make this an issue!

	#Color management is simple: openlut doesn't touch your data, unless you tell it to with a Transform. So, the data that goes in, goes out, unless a Transform was applied.

if __name__ == "__main__" :
	runTest('img_test', 'testpath')
