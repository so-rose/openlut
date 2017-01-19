import sys, os, os.path

import numpy as np

#~ import skimage as si
#~ import skimage.io
#~ si.io.use_plugin('freeimage')

#~ from PIL import Image
#~ import tifffile as tff

import wand
import wand.image
import wand.display

from wand.api import library

#~ library.MagickSetCompressionQuality.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
#~ library.MagickSetCompression.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

#~ COMPRESS_TYPES = dict(zip(wand.image.COMPRESSION_TYPES, tuple(map(ctypes.c_int, range(len(wand.image.COMPRESSION_TYPES))))))

from . import gamma
from .LUT import LUT
from .Viewer import Viewer

class ColMap :
	def __init__(self, rgbArr) :
		self.rgbArr = np.array(rgbArr, dtype=np.float32) #Enforce 32 bit floats. Save memory.
		
	def fromIntArray(imgArr) :
		bitDepth = int(''.join([i for i in str(imgArr.dtype) if i.isdigit()]))
		return ColMap(np.divide(imgArr.astype(np.float64), 2 ** bitDepth - 1))
		
#Operations - returns new ColMaps.
	def apply(self, transform) :
		'''
		Applies a Transform object by running its apply method.
		'''
		#~ return transform.apply(self)
		return ColMap(transform.sample(self.asarray()))
		
#IO Functions
	@staticmethod
	def open(path) :
		'''
		Opens 8 and 16 bit images of many formats.
		'''
		
		try :
			openFunction = {
				"exr" : ColMap.openWand,
				"dpx" : ColMap.openWand,
			}[path[path.rfind('.') + 1:]]
			
			return openFunction(path) #Any fancy formats will go here.
		except :
			#Fallback to opening using Wand.
			return ColMap.openWand(path)
		
	#Vendor-specific open methods.
	
	#~ def openSci(path) :
		#~ return ColMap.fromIntArray(si.io.imread(path)[:,:,:3])
	
	@staticmethod
	def openWand(path) :
		'''
		Open a file using the Wand ImageMagick binding.
		'''
		with wand.image.Image(filename=path) as img:
			#Quick inverse sRGB transform, to undo what Wand did - but not for exr's, which are linear bastards.
			if img.format != 'EXR' :
				img.colorspace = 'srgb'
				img.transform_colorspace('rgb')
			
				img.colorspace = 'srgb' if img.format == 'DPX' else 'rgb' #Fix for IM's dpx bug.
			
			return ColMap.fromIntArray(np.fromstring(img.make_blob("RGB"), dtype='uint{}'.format(img.depth)).reshape(img.height, img.width, 3))
	
	@staticmethod
	def fromBinary(binData, fmt, width=None, height=None) :
		'''
		Using the Wand blob functionality, creates a ColMap from binary data. Set binData to sys.stdin.buffer.read() to activate piping!
		'''
		with wand.image.Image(blob=binData, format=fmt, width=width, height=height) as img:
			return ColMap.fromIntArray(np.fromstring(img.make_blob("RGB"), dtype='uint{}'.format(img.depth)).reshape(img.height, img.width, 3))
	
	@staticmethod
	def toBinary(self, fmt, depth=16) :
		'''
		Using Wand blob functionality
		'''
		with self.asWandImg(depth) as img :
			img.format = fmt
			return img.make_blob()
	
	@staticmethod
	def save(self, path, compress = None, depth = None) :
		'''
		Save the image. The filetype will be inferred from the path, and the appropriate backend will be used.
		
		Compression scheme will be applied based on the backend compatiblity. Wand compression types can be used: Browse then
		at http://docs.wand-py.org/en/0.4.3/wand/image.html#wand.image.COMPRESSION_TYPES .
		'''
		if depth is None: depth = 16
		try :
			saveFunction = {
				"exr" : self.saveWand,
				"dpx" : self.saveWand,
				"tif" : self.saveWand,
				"tiff": self.saveWand
			}[path[path.rfind('.') + 1:]]
			
			return saveFunction(path, compress, depth)
		except :
			#Fallback to saving using Wand.
			self.saveWand(path, compress, depth)
			
	#Vendor-specific save methods
			
	def saveWand(self, path, compress = None, depth = 16) :
		data = self.apply(LUT.lutFunc(gamma.sRGB)) if path[path.rfind('.')+1:] == 'dpx' else self
		i = data.asWandImg(depth)
		
		i.colorspace = 'srgb' #Make sure it saves without a colorspace transformation.
		
		#~ if compress :
			#~ library.MagickSetCompression(i.wand, 'rle')
			
			#~ i.compression = 'lzma'
			#~ i.compression_quality = 80

		i.save(filename=path)
		
	#~ def saveSci(self, path, compress = None, depth = 16) :
		#~ if compress is not None: raise ValueError('Scipy Backend cannot compress the output image!')
		#~ si.io.imsave(path, self.asIntArray())
		
	#Display Functions
	
	@staticmethod
	def display(path, width = 1200) :
		'''
		Shows an image at a path without making a ColMap.
		'''
		
		img = ColMap.open(path).rgbArr
		aspectRatio = img.shape[0]/img.shape[1]
			
		xRes = width
		yRes = int(xRes * aspectRatio)
		
		Viewer.run(img, xRes, yRes, title = os.path.basename(path))
		
	def show(self, width = 1200) :
		#Use my custom OpenGL viewer!
		Viewer.run(self.rgbArr, width, int(width * self.rgbArr.shape[0]/self.rgbArr.shape[1]))
		
	@staticmethod
	def wandShow(wandImg) :
		#Do a quick sRGB transform for viewing. Must be in 'rgb' colorspace for this to take effect.
		wandImg.transform_colorspace('srgb')
		
		wand.display.display(wandImg)
		
		wandImg.transform_colorspace('rgb') #This transforms it back to linearity.
		
		
	#Data Form Functions
	def asWandImg(self, depth = 16) :
		#~ i = wand.image.Image(blob=self.asarray().tostring(), width=np.shape(self.rgbArr)[1], height=np.shape(self.rgbArr)[0], format='RGB') #Float Array
		i = wand.image.Image(blob=self.asIntArray(depth).tostring(), width=np.shape(self.rgbArr)[1], height=np.shape(self.rgbArr)[0], format='RGB')
		i.colorspace = 'rgb' #Specify, to Wand, that this image is to be treated as raw, linear, data.
		
		return i
		
	def asarray(self) :
		"""
		Returns the base float array.
		"""
		return self.rgbArr
		
	def asIntArray(self, depth = 16, us = True) :
		u = 'u' if us else ''
		return np.multiply(self.rgbArr.clip(0, 1), 2.0 ** depth - 1).astype("{0}int{1}".format(u, depth))
		
		
	#Overloads
	def __repr__(self) :
		return 'ColMap( \n\trgbArr = {0}\n)'.format('\n\t\t'.join([line.strip() for line in repr(self.rgbArr).split('\n')]))
