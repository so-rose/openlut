import sys, os, os.path

from functools import reduce

import numpy as np

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

from .lib import olOpt as olo

class ColMap :
	'''
	The ColMap class stores an image in its 32 bit float internal working space.
	
	:var DEPTHS: A dictionary of depths in relation to the Depths dictionary.
	
	ColMaps are initialized by default with 0's; a black image. You can use
	`open` to load a path, :py:func:`~fromArray` to load from a numpy array, or :py:func:`~fromBinary` to load from
	a binary representation (useful in pipes).
	
	:param shape: The numpy-style shape of the empty image. Specify width, then height.
	:type shape: tuple[int, int] or tuple[int, int, int]
	:param depth: The integer depth used for int format's input and output. Set to DEPTHS['full'] by default.
	:type depth: int or None
	
	:return: An empty ColMap, holding a black image of specified shape.
	:raises ValueError: When trying to use unsupported bit depth.
	:raises ValueError: When using invalid image shape.
	'''
	
	DEPTHS = {	'default'	: None,
				'comp'		: 8,
				'half'		: 16,
				'full'		: 32,
				'double'	: 64
	}
	
#Constructors
	def __init__(self, shape, depth = None) :
		if depth not in ColMap.DEPTHS.values :
			raise ValueError('Bit depth not supported! Supported bit depths: {}'.format(', '.join(ColMap.DEPTHS.values)))
		
		if len(shape) not in (2, 3) :
			raise ValueError('Please use a valid numpy image array shape!')
		
		self.depth = depth if depth is None else ColMap.DEPTHS['full'] #This represents the real precision of data.
		self.rgbArr = np.zeros((shape[0], shape[1], 3), dtype=np.float32)
		
	@staticmethod
	def fromArray(imgArr) :
		'''
		Initialize a ColMap from a numpy array of either float or int type (containing an image).
		
		See :py:class:`~ColMap` initialization for a lower-level constructor.
		
		:param imgArr: The numpy image array. Must have shape (width, height, 3)
		:param depth: The integer depth used for int format's input and output. None will use highest available.
		:type depth: int or None
		
		:return: A ColMap containing the image represented in imgArr.
		:raises ValueError: When trying to use unsupported array data type
		'''
		
		#Infer bitDepth from array to create new array, nArr, which we'll use to make our ColMap.
		
		if issubclass(imgArr.dtype.type, np.integer) : #If it's an integer.
			bitDepth = int(''.join([i for i in str(imgArr.dtype) if i.isdigit()]))
			
			nArr = np.divide(imgArr.astype(np.float32), 2 ** bitDepth - 1)
			
		elif issubclass(imgArr.dtype.type, np.floating) : #It it's a float.
			#If we're dealing with an np.float16 array, we can't exactly start giving 32 bit output.
			if int(''.join([i for i in str(imgArr.dtype) if i.isdigit()])) == 16 :
				bitDepth = 16
			else :
				bitDepth = None
				
			nArr = np.array(imgArr, dtype=np.float32)
			
		else :
			raise ValueError('The input image array uses an invalid data type {}! Please use any np.int or np.float variant!'.format(imgArr.dtype.type))
		
				
		#We're taking over the creation of img.rgbArr, so we need to do different error checking of our own.
		if len(nArr.shape) not in (2, 3) :
			raise ValueError('Please use a valid numpy image array shape!')
			
		elif len(nArr.shape) == 2 :
			
			#If we're dealing with a greyscale image, then we need to convert it to RGB using an optimized C++ function.
			nArr = olo.grey_to_rgb(nArr.reshape(reduce(lambda a, b: a*b, nArr.shape))).reshape((nArr.shape[0], nArr.shape[1], 3))
		
		img = ColMap(nArr.shape, depth=bitDepth)
		img.rgbArr = nArr
		
		return img
		
	@staticmethod
	def fromBinary(binData, fmt, width=None, height=None) :
		'''
		Construct a ColMap from an image in binary form. See :py:func:`~ColMap.toBinary` for the inverse.
		
		* This won't work for greyscale data - it's assumed to be RGB.
		
		:param bin binData: The binary data blob to open.
		:param str fmt: Wand needs to know what image format the binary data being thrown at it is in! See https://www.imagemagick.org/script/formats.php .
		:param str width: You may specify a specific width if you're having problems.
		:param str height: You may specify a specific height if you're having problems.
		:return: The image, as a ColMat.
		:rtype: :py:class:`~ColMap`
		
		This is great for pipes, where you're receiving binary data through stdin.
			* Set binData to `sys.stdin.buffer.read()` in a script to pipe data into it!
			
		**NOTE: Uses Wand's "blob" functionality, and as such incurs Wand's limitations.**
		'''
		with wand.image.Image(blob=binData, format=fmt, width=width, height=height) as img:
			
			return ColMap.fromArray(np.fromstring(img.make_blob("RGB"), dtype='uint{}'.format(img.depth)).reshape(img.height, img.width, 3))
	
		
	@staticmethod
	def open(path) :
		'''
		Construct a ColMap from an image on the disk.
		
		:param str path: The image path to open.
		:return: The image, as a ColMat.
		:rtype: :py:class:`~ColMap`
		
		ColMap currently uses ImageMagick to open a wide range of formats, including:
		
		* **EXR**: The industry standard for HDR, wide-gamut, linear-encoded images.
		* **DPX**: An older production format.
		* **PNG**: Can store 16-bit images well. Usually quite slow.
		* *Any other IM-supported formats...* See https://www.imagemagick.org/script/formats.php
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
		
#Operations - returns new ColMaps.
	def apply(self, transform) :
		'''
		Apply an image transformation, in the form of a subclass of :py:class:`~Transform`.
		
		You can apply LUTs, gamma functions, matrices - simply insert an instance of :py:class:`~LUT`,
		:py:class:`~Func`, :py:class:`~ColMat`, or any other :py:class:`~Transform` object to apply it
		to the image!
		
		:param transform: An image transform.
		:type transform: :py:class:`~Transform`
		:return: A transformed ColMap.
		'''
		return ColMap.fromArray(transform.sample(self.asarray()))
		
#Vendor-specific open methods.
	@staticmethod
	def openWand(path) :
		'''
		Vendor-specific :py:func:`~ColMap.open` function. See :py:func:`~ColMap.open`
		
		:param str path: The image path to open.
		:return: The image, as a ColMat.
		:rtype: :py:class:`~ColMap`
		'''
		
		with wand.image.Image(filename=path) as img:
			#Quick inverse sRGB transform, to undo what Wand did - but not for exr's, which are linear bastards.
			if img.format != 'EXR' :
				img.colorspace = 'srgb'
				img.transform_colorspace('rgb')
			
				img.colorspace = 'srgb' if img.format == 'DPX' else 'rgb' #Fix for IM's dpx bug.
			
			return ColMap.fromArray(np.fromstring(img.make_blob("RGB"), dtype='uint{}'.format(img.depth)).reshape(img.height, img.width, 3))
	
	def save(self, path, compress = None, depth = None) :
		'''
		Save a ColMap to an image file on the disk.
		
		:param str path: The path to save the image file at. The extension specified determines the output format.
		:param compress: Compression options passed to the vendor. Currently broken.
		:type compress: str or None
		:param depth: You may override the ColMap's depth if you wish.
		:type depth: int or None
		
		
		ColMap currently uses ImageMagick to save a wide range of formats, including:
		
		* **EXR**: The industry standard for HDR, wide-gamut, linear-encoded images.
		* **DPX**: An older production format.
		* **PNG**: Can store 16-bit images well. Usually quite slow.
		* *Any other IM-supported formats...* See https://www.imagemagick.org/script/formats.php
		
		**NOTE: EXRs are only saveable as 16-bit integer, with no compression options. This is an IM/Wand library limitation.**
		'''
		
		if depth not in ColMap.DEPTHS.values :
			raise ValueError('Bit depth not supported! Supported bit depths: {}'.format(', '.join(ColMap.DEPTHS.values)))
		
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

	def saveWand(self, path, compress = None, depth = None) :
		'''
		Vendor-specific :py:func:`~ColMap.save` function. See :py:func:`~ColMap.save`
		
		:param str path: The image path to save to.
		:param compress: Compression options passed to Wand. Currently broken.
		:param depth: You may override the ColMap's depth if you wish.
		:type depth: int or None
		
		**NOTE: EXRs are only saveable as 16-bit integer, with no compression options. This is an IM/Wand library limitation.**
		'''
		
		if depth not in ColMap.DEPTHS.values :
			raise ValueError('Bit depth not supported! Supported bit depths: {}'.format(', '.join(ColMap.DEPTHS.values)))
		
		data = self.apply(LUT.lutFunc(gamma.sRGB)) if path[path.rfind('.')+1:] == 'dpx' else self
		i = data.asWandImg(depth)
		
		i.colorspace = 'srgb' #Make sure it saves without a colorspace transformation.
		
		#~ if compress :
			#~ library.MagickSetCompression(i.wand, 'rle')
			
			#~ i.compression = 'lzma'
			#~ i.compression_quality = 80

		i.save(filename=path)
		

#Display Functions
	
	@staticmethod
	def display(path, width = 1000) :
		'''
		Display an image at a path on the disk, using the builtin OpenGL Viewer.
		
		:param width: The desired width of the viewer; the height is automatically gleaned from the aspect ratio.
		
		For the viewer source code, see :py:class:`~Viewer`.
		'''
		
		img = ColMap.open(path).rgbArr
		aspectRatio = img.shape[0]/img.shape[1]
			
		xRes = width
		yRes = int(xRes * aspectRatio)
		
		Viewer.run(img, xRes, yRes, title = os.path.basename(path))
		
	def show(self, width = 1000) :
		'''
		Display this ColMap using the builtin OpenGL Viewer.
		
		:param width: The desired width of the viewer; the height is automatically gleaned from the aspect ratio.
		
		For the viewer source code, see :py:class:`~Viewer`.
		'''
		
		#Use my custom OpenGL viewer!
		Viewer.run(self.rgbArr, width, int(width * self.rgbArr.shape[0]/self.rgbArr.shape[1]))
		

#Data Output Types
	def asWandImg(self, depth = None) :
		'''
		Output this ColMap as a Wand image.
				
		:param depth: You may override the ColMap's depth if you wish.
		:type depth: int or None
		:return: The Wand Image.
		:rtype: wand.image
		
		See http://docs.wand-py.org/en/0.4.4/index.html for Wand docs.
		'''
		
		if depth not in ColMap.DEPTHS.values :
			raise ValueError('Bit depth not supported! Supported bit depths: {}'.format(', '.join(ColMap.DEPTHS.values)))
		
		if depth is None :
			d = ColMap.DEPTHS['half'] if self.depth >= ColMap.DEPTHS['half'] else self.depth #Highest is half - 16.
		else :
			d = depth
		
		#~ i = wand.image.Image(blob=self.asarray().tostring(), width=np.shape(self.rgbArr)[1], height=np.shape(self.rgbArr)[0], format='RGB') #Float Array
		i = wand.image.Image(blob=self.asIntArray(d).tostring(), width=np.shape(self.rgbArr)[1], height=np.shape(self.rgbArr)[0], format='RGB')
		i.colorspace = 'rgb' #Specify, to Wand, that this image is to be treated as raw, linear, data.
		
		return i
		
			
	def toBinary(self, fmt, depth=None) :
		'''
		Output this ColMap in binary form. See :py:func:`~ColMap.fromBinary` for the inverse.
				
		:param str fmt: Wand needs to know what format to output! See https://www.imagemagick.org/script/formats.php .
		:param depth: You may override the ColMap's bit depth if you wish.
		:type depth: int or None
		:return: The image, as a ColMat.
		:rtype: :py:class:`~ColMap`
		
		This is great for pipes, where you're sending binary data through stdout.
			* Use the return value as the argument of sys.stdout.write() to pipe the image to other applications!
			
		**NOTE: Uses Wand's "blob" functionality, and as such incurs Wand's limitations.**
		'''
		
		if depth not in ColMap.DEPTHS.values :
			raise ValueError('Bit depth not supported! Supported bit depths: {}'.format(', '.join(ColMap.DEPTHS.values)))
		
		with self.asWandImg(d) as img :
			img.format = fmt
			return img.make_blob()
		
	def asarray(self) :
		"""
		Returns the internal np.float32 image array directly.
		
		:return: The internal numpy array.
		:rtype: np.array
		"""
		return self.rgbArr
		
	def asIntArray(self, depth = None, us = True) :
		"""
		Returns the internal image array as an int array.
		
		:param depth: You may override the ColMap's bit depth if you wish.
		:type depth: int or None
		:param bool us: True will output unsigned ints, False will output signed ints.
		:return: The internal numpy array.
		:rtype: np.array
		"""
		
		if depth not in ColMap.DEPTHS.values :
			raise ValueError('Bit depth not supported! Supported bit depths: {}'.format(', '.join(ColMap.DEPTHS.values)))
		
		if depth is None :
			d = self.depth #No limits here.
		else :
			d = depth
		
		u = 'u' if us else '' #Unsigned or no?
		return np.multiply(self.rgbArr.clip(0, 1), 2.0 ** depth - 1).astype("{0}int{1}".format(u, depth))
		
		
#Overloads
	def __repr__(self) :
		return 'ColMap.fromArray( \n\trgbArr = {0}\n)'.format('\n\t\t'.join([line.strip() for line in repr(self.rgbArr).split('\n')]))
