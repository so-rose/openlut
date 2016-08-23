#!/usr/bin/env python3.5

'''
openlut: A package for managing and applying 1D and 3D LUTs.

Color Management: openlut deals with the raw RGB values, does its work, then puts out images with correct raw RGB values - a no-op.

Dependencies:
	-numpy: Like, everything.
	-wand: Saving/loading all images.
	-numba: 38% speedup for matrix math.
	
	-scipy - OPTIONAL: For spline interpolation.
	
Easily get all deps: sudo pip3 install numpy wand numba scipy

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

import sys, os, math, abc, ctypes

import multiprocessing as mp
from functools import reduce
import operator as oper

MOD_SCIPY = False
try :
	from scipy.interpolate import splrep, splev
	MOD_SCIPY = True
except :
	pass

import numpy as np
import numba

#~ import skimage as si
#~ import skimage.io
#~ si.io.use_plugin('freeimage')

#~ from PIL import Image
#~ import tifffile as tff

import wand
import wand.image
import wand.display

from wand.api import library

library.MagickSetCompressionQuality.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
library.MagickSetCompression.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

COMPRESS_TYPES = dict(zip(wand.image.COMPRESSION_TYPES, tuple(map(ctypes.c_int, range(len(wand.image.COMPRESSION_TYPES))))))



#~ from lib.files import Log #For Development

class Transform :
	def apply(self, cMap) :
		"""
		Applies this transformation to a ColMap.
		"""
		return ColMap(self.sample(cMap.asarray()))
		
	@abc.abstractmethod
	def sample(self, fSeq) :
		"""
		Samples the Transformation.
		"""
		
	def spSeq(seq, outLen) :
		"""
		Utility function for splitting a sequence into equal parts, for multithreading.
		"""
		perfSep = (1/outLen) * len(seq)
		return list(filter(len, [seq[round(perfSep * i):round(perfSep * (i + 1))] for i in range(len(seq))])) if len(seq) > 1 else seq
		
class ColMap :
	def __init__(self, rgbArr) :
		self.rgbArr = rgbArr
		
	def fromIntArray(imgArr) :
		bitDepth = int(''.join([i for i in str(imgArr.dtype) if i.isdigit()]))
		return ColMap(np.divide(imgArr.astype(np.float64), 2 ** bitDepth - 1))
		
#Operations - returns new ColMaps.
	def apply(self, transform) :
		'''
		Applies a Transform object by running its apply method.
		'''
		return transform.apply(self)
		
#IO Functions
		
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
		
	def openWand(path) :
		'''
		Open a file using the Wand ImageMagick binding.
		'''
		with wand.image.Image(filename=path) as img:
			#Quick inverse sRGB transform, to undo what Wand did.
			img.colorspace = 'srgb'
			img.transform_colorspace('rgb')
			
			img.colorspace = 'srgb' if img.format == 'DPX' else 'rgb' #Fix for IM's dpx bug.
			
			return ColMap.fromIntArray(np.fromstring(img.make_blob("RGB"), dtype='uint{}'.format(img.depth)).reshape(img.height, img.width, 3))
	
	
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
		data = self.apply(LUT.lutFunc(Gamma.sRGB)) if path[path.rfind('.')+1:] == 'dpx' else self
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
		
	#~ def savePil(self, path, compress = None, depth = 8) :
		#~ if compress is not None: raise ValueError('Scipy Backend cannot compress the output image!')
		#~ if depth != 8: raise ValueError('Cannot save non-8 bit image using PIL.')
		#~ self.asPilImg().save(path)
		
		
	def show(self) :
		#~ ColMap.pilShow(self.apply(LUT.lutFunc(Gamma.sRGB)).asPilImg())
		ColMap.wandShow(self.asWandImg())
		
	#~ def pilShow(pilImg) :
		#~ pilImg.show()
		
	def wandShow(wandImg) :
		#Do a quick sRGB transform for viewing. Must be in 'rgb' colorspace for this to take effect.
		wandImg.transform_colorspace('srgb')
		
		wand.display.display(wandImg)
		
		wandImg.transform_colorspace('rgb') #This transforms it back to linearity.
		
		
	#Data Form Functions
	#~ def asPilImg(self) :
		#~ return Image.fromarray(self.asIntArray(8), mode='RGB')
		
	def asWandImg(self, depth = 16) :
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
		
class LUT(Transform) :
	def __init__(self, dims = 1, size = 16384, title = "openlut_LUT", array = None, iRange = (0.0, 1.0)) :	
		'''
		Create an identity LUT with given dimensions (1 or 3), size, and title.
		'''	
		if array is not None :
			LUT.lutArray(array, size, dims, title)
		else :
			if dims != 1 and dims != 3: raise ValueError("Dimensions must be 1 or 3!")
			
			self.title = title #The title.
			self.size = size #The size. 1D LUTs: size numbers. 3D LUTs: size x size x size numbers.
			self.range = iRange #The input range - creates data or legal LUTs. Should work fine, but untested.
			self.dims = dims #The dimensions. 1 or 3; others aren't accepted.
			self.ID = np.linspace(self.range[0], self.range[1], self.size) #Read Only.
			
			if dims == 1 :
				self.array = np.linspace(self.range[0], self.range[1], self.size) #Size number of floats.
			elif dims == 3 :
				print("3D LUT Not Implemented!")
				#~ self.array = np.linspace(self.range[0], self.range[1], self.size**3).reshape(self.size, self.size, self.size) #Should make an identity size x size x size array.
		
	def lutFunc(func, size = 16384, dims = 1, title="openlut_FuncGen") :
		'''
		Creates a LUT from a simple function.
		'''
		if dims == 1 :
			lut = LUT(dims=dims, size=size, title=title)
			
			vFunc = np.vectorize(func, otypes=[np.float])
			lut.array = vFunc(lut.array)
			
			return lut
		elif dims == 3 :
			print("3D LUT Not Implemented!")
			
	def lutArray(array, title="Array_Generated") :
		'''
		Creates a LUT from a float array. Elements must be in range [0, 1].
		'''
		if len(np.shape(array)) == 1 :
			lut = LUT(dims=1, size=len(array), title=title)
			lut.array = array
			
			return lut
		elif len(np.shape(array)) == 3 :
			print("3D LUT Not Implemented!")
		else :
			raise ValueError("lutArray input must be 1D or 3D!")
		
#LUT Functions.
	def __interp(q, cpu, spSeq, ID, array, spl) :
		if spl :
			q.put( (cpu, splev(spSeq, splrep(ID, array))) ) #Spline Interpolation. Pretty quick, considering.
		else :
			q.put( (cpu, np.interp(spSeq, ID, array)) )
	
	def sample(self, fSeq, spl=True) :
		'''
		Sample the LUT using a flat float sequence (ideally a numpy array; (0..1) ).
		
		Each n (dimensions) clump of arguments will be used to sample the LUT. So:
			1D LUT: in1, in2, in3 --> out1, out2, out3
			*Min 1 argument.
			
			3D LUT: inR, inG, inB --> outR, outG, outB
			*Min 3 arguments, len(arguments) % 3 must equal 0.
			
		Returns a numpy array with identical shape to the input array.
		'''
				
		fSeq = np.array(fSeq)
		if self.dims == 1 :
			#~ return np.interp(spSeq, self.ID, self.array)
			
			#If scipy isn't loaded, we can't use spline interpolation!
			if (not MOD_SCIPY) or self.size > 1023: spl = False # Auto-adapts big LUTs to use the faster, more brute-forceish, linear interpolation.
			#~ spl = True
			out = []
			q = mp.Queue()
			splt = Transform.spSeq(fSeq, mp.cpu_count())
			for cpu in range(mp.cpu_count()) :
				p = mp.Process(target=LUT.__interp, args=(q, cpu, splt[cpu], self.ID, self.array, spl))
				p.start()
				
			for num in range(len(splt)) :
				out.append(q.get())
				
			return np.concatenate([seq[1] for seq in sorted(out, key=lambda seq: seq[0])], axis=0)
			
		elif self.dims == 3 :
			print("3D LUT Not Implemented!")
			
	def resized(self, newSize) :
		if newSize == self.size: return self
			
		fac = newSize / self.size
		
		useSpl = self.size < newSize #If the new size is lower, we use Linear interpolation. If the new size is higher, we use Spline interpolation.
		if self.size < 128: useSpl = True #If the current size is too low, use spline regardless.
		
		if self.dims == 1 :
			newID = np.linspace(self.range[0], self.range[1], newSize)
			return LUT.lutArray(self.sample(newID, spl=useSpl), title="Resized to {0}".format(newSize))
		if self.dims == 3 :
			print("3D LUT Not Implemented")
	
#IO Functions.
				
	def open(path) :
		'''
		Opens any supported file format, located at path.
		'''
		openFunction = {
			"cube" : LUT.openCube,
		}[path[path.rfind('.') + 1:]]
		
		return openFunction(path)
			
	def openCube(path) :
		'''
		Opens .cube files. They must be saved with whitespaces. Referenced by open().
		'''
		lut = LUT() #Mutable luts are not reccommended for users.
	
		with open(path, 'r') as f :
			i = 0
			for line in f :
				#~ if not line.strip(): continue
				sLine = line.strip()
				if not sLine: continue
				
				if sLine[0] == '#': continue
				
				index = sLine[:sLine.find(' ')]
				data = sLine[sLine.find(' ') + 1:]
				
				if index == "TITLE": lut.title = data.strip('"'); continue
				if index == "LUT_1D_SIZE": lut.dims = 1; lut.size = int(data); continue
				if index == "LUT_3D_SIZE": lut.dims = 3; lut.size = int(data); continue
				
				if index == "LUT_1D_INPUT_RANGE": lut.range = (float(data[:data.find(' ')]), float(data[data.find(' ') + 1:])); continue
								
				if lut.dims == 1 and sLine[:sLine.find(' ')] :
					lut.array[i] = float(sLine[:sLine.find(' ')])
					i += 1
				elif lut.dims == 3 :
					print("3D LUT Not Implemened!")
				
		return lut
		
	def save(self, path) :
		'''
		Method that saves the LUT in a supported format, based on the path.
		'''
		saveFunction = {
			"cube" : self.saveCube,
			
		
		}[path[path.rfind('.') + 1:]]
		
		saveFunction(path)
		
	def saveCube(self, path) :
		with open(path, 'w') as f :
			print('TITLE', '"{}"'.format(self.title), file=f)
			
			if self.dims == 1 :
				print('LUT_1D_SIZE', '{}'.format(self.size), file=f)
				print('LUT_1D_INPUT_RANGE', '{0:.6f} {1:.6f}'.format(*self.range), file=f)
				print('# Created by openlut.\n', file=f)
				
				for itm in self.array :
					entry = '{0:.6f}'.format(itm)
					print(entry, entry, entry, file=f)
			elif self.dims == 3 :
				print("3D LUT Not Implemented!")
		
#Overloaded functions
	
	def __iter__(self) :
		if dims == 1 :
			return iter(self.array)
		elif dims == 3 :
			iArr = self.array.reshape(self.dims, self.size / self.dims) #Group into triplets.
			return iter(iArr)
		
	def __getitem__(self, key) :
		return self.sample(key)
		
	def __repr__(self) :
		return 'LUT(\tdims = {0},\n\tsize = {1},\n\ttitle = "{2}"\n\tarray = {3}\n)'.format(self.dims, self.size, self.title, '\n\t\t'.join([line.strip() for line in repr(self.array).split('\n')]))
		
class Gamma(Transform) :
	def __init__(self, func) :
		self.func = func
		
	#Gamma Methods
	def __gamma(q, cpu, f, spSeq) :
		q.put( (cpu, f(spSeq)) )
	
	def sample(self, fSeq) :
		fSeq = np.array(fSeq)
		fVec = np.vectorize(self.func)
		
		out = []
		q = mp.Queue()
		splt = Transform.spSeq(fSeq, mp.cpu_count())
		for cpu in range(mp.cpu_count()) :
			p = mp.Process(target=Gamma.__gamma, args=(q, cpu, fVec, splt[cpu]))
			p.start()
			
		for num in range(len(splt)) :
			out.append(q.get())
			
		return np.concatenate([seq[1] for seq in sorted(out, key=lambda seq: seq[0])], axis=0) if len(fSeq) > 1 else self.func(fSeq[0])
		
		return fVec(fSeq) if len(fSeq) > 1 else self.func(fSeq[0])
	
	#Static Gamma Functions (partly adapted from MLRawViewer)
	
	def lin(x): return x
	
	def sRGB(x) :
		'''
		sRGB formula. Domain must be within [0, 1].
		'''
		return ( (1.055) * (x ** (1.0 / 2.4)) ) - 0.055 if x > 0.0031308 else x * 12.92
	def sRGBinv(x) :
		'''
		Inverse sRGB formula. Domain must be within [0, 1].
		'''
		return ((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92
		
	def Rec709(x) :
		'''
		Rec709 formula. Domain must be within [0, 1].
		'''
		return 1.099 * (x ** 0.45) - 0.099 if x >= 0.018 else 4.5 * x
		
	def ReinhardHDR(x) :
		'''
		Reinhard Tonemapping formula. Domain must be within [0, 1].
		'''
		return x / (1.0 + x)
	
	def sLog(x) :
		'''
		sLog 1 formula. Domain must be within [0, 1]. See https://pro.sony.com/bbsccms/assets/
		files/mkt/cinema/solutions/slog_manual.pdf .
		'''
		return ( 0.432699 * math.log(x + 0.037584, 10.0) + 0.616596) + 0.03 
		
	def sLog2(x) :
		'''
		sLog2 formula. Domain must be within [0, 1]. See https://pro.sony.com/bbsccms/assets/files/micro/dmpc/training/S-Log2_Technical_PaperV1_0.pdf .
		'''
		return ( 0.432699 * math.log( (155.0 * x) / 219.0 + 0.037584, 10.0) + 0.616596 ) + 0.03
		
	def sLog3(x) :
		'''
		Not yet implemented. See http://community.sony.com/sony/attachments/sony/large-sensor-camera-F5-F55/12359/2/TechnicalSummary_for_S-Gamut3Cine_S-Gamut3_S-Log3_V1_00.pdf .
		'''
		return x
		
	def DanLog(x) :
		return (10.0 ** ((x - 0.385537) / 0.2471896) - 0.071272) / 3.555556 if x > 0.1496582 else (x - 0.092809) / 5.367655
		
	def DanLoginv(x) :
		pass
		
		
class TransMat(Transform) :
	def __init__(self, *mats) :
		'''
		Initializes a combined 3x3 Transformation Matrix from any number of input matrices. These may be numpy arrays, matrices,
		other TransMats, or any combination thereof.
		'''
		if len(mats) == 1 :
			mat = mats[0]
			
			if isinstance(mat, TransMat) :
				self.mat = mat.mat #Support a copy constructor.
			else :
				self.mat = np.array(mat) #Simply set self.mat with the numpy array version of the mat.
		elif len(mats) > 1 :
			self.mat = TransMat.__mats(*[TransMat(mat) for mat in mats]).mat
		elif not mats :
			self.mat = np.identity(3)
		
	def __mats(*inMats) :
		'''
		Initialize a combined Transform matrix from several input TransMats.
		'''
		return TransMat(reduce(TransMat.__mul__, reversed(inMats))) #Works because multiply is actually non-commutative dot.
		#This is why we reverse inMats.
		
	@numba.jit(nopython=True)
	def __optDot(img, mat, shp, out) :
		shaped = img.reshape((shp[0] * shp[1], shp[2])) #Flatten to 2D array for iteration over colors.
		i = 0
		while i < shp[0] * shp[1] :
			res = np.dot(mat, shaped[i])
			out[i] = res
			i += 1
			
	def __applMat(q, cpu, shp, mat, img3D) :
		out = np.zeros((shp[0] * shp[1], shp[2]))
		TransMat.__optDot(img3D, mat, shp, out)
		q.put( (cpu, out.reshape(shp)) )
	
	def sample(self, fSeq) :
		shp = np.shape(fSeq)
		if len(shp) == 1 :
			return self.mat.dot(fSeq)
		if len(shp) == 3 :
			cpus = mp.cpu_count()
			out = []
			q = mp.Queue()
			splt = Transform.spSeq(fSeq, cpus)
			for cpu in range(cpus) :
				p = mp.Process(target=TransMat.__applMat, args=(q, cpu, np.shape(splt[cpu]), self.mat, splt[cpu]))
				p.start()
				
			for num in range(len(splt)) :
				out.append(q.get())
				
			return np.concatenate([seq[1] for seq in sorted(out, key=lambda seq: seq[0])], axis=0)
			
			#~ out = np.zeros((shp[0] * shp[1], shp[2]))
			#~ TransMat.__optDot(fSeq, self.mat, shp, out)
			#~ return out.reshape(shp)
			
			#~ return np.array([self.mat.dot(col) for col in fSeq.reshape(shp[0] * shp[1], shp[2])]).reshape(shp)
			
			#~ p = mp.Pool(mp.cpu_count())
			#~ return np.array(list(map(self.mat.dot, fSeq.reshape(shp[0] * shp[1], shp[2])))).reshape(shp)
		#~ return fSeq.dot(self.mat)
		
	def inv(obj) :
		if isinstance(obj, TransMat) : #Works on any TransMat object - including self.
			return TransMat(np.linalg.inv(obj.mat))
		else : #Works on raw numpy arrays as well.
			return np.linalg.inv(obj)
		
	def transpose(self) :
		return TransMat(np.transpose(self.mat))
		
	#Overloading
	def __mul__(self, other) :
		'''
		* implements matrix multiplication.
		'''
		if isinstance(other, TransMat) :
			return TransMat(self.mat.dot(other.mat))
		elif isinstance(other, float) or isinstance(other, int) :
			return TransMat(np.multiply(self.mat, other))
		elif isinstance(other, np.ndarray) or isinstance(other, np.matrixlib.defmatrix.matrix) :
			return TransMat(self.mat.dot(np.array(other)))
		else :
			raise ValueError('Invalid multiplication arguments!')
			
	__rmul__ = __mul__
	
	def __add__(self, other) :
		if isinstance(other, TransMat) :
			return TransMat(self.mat + other.mat)
		elif isinstance(other, np.ndarray) or isinstance(other, np.matrixlib.defmatrix.matrix) :
			return TransMat(self.mat + np.array(other))
		else :
			raise ValueError('Invalid addition arguments!')
			
	__radd__ = __add__
	
	def __pow__(self, other) :
		'''
		** implements direct multiplication. You usually don't want this.
		'''
		if isinstance(other, TransMat) :
			return TransMat(self.mat * other.mat)
		elif isinstance(other, float) or isinstance(other, int) :
			return TransMat(np.multiply(self.mat, other))
		elif isinstance(other, np.ndarray) or isinstance(other, np.matrixlib.defmatrix.matrix) :
			return TransMat(self.mat * np.array(other))
		else :
			raise ValueError('Invalid multiplication arguments!')
			
	def __invert__(self) :
		return self.inv()
	
	def __len__(self) :
		return len(self.mat)
		
	def __getitem__(self, key) :
		return self.mat[key]
		
	def __iter__(self) :
		return iter(self.mat)
		
	def __repr__(self) :
		return "\nTransMat (\n{0}  )\n".format(str(self.mat))
		
	
			
		
		
	#Static Transmat Matrices -- all go from ACES to <gamut name>. <gamut name>inv functions go from the gamut to ACES.
	#Converted (CIECAT02) D65 Illuminant for all.
	
	XYZ = np.array(
			[
				0.93863095, -0.00574192, 0.0175669,
				0.33809359, 0.7272139, -0.0653075,
				0.00072312, 0.00081844, 1.08751619
			]
		).reshape(3, 3)
		
	XYZinv = np.array(
			[
				1.06236611, 0.00840695, -0.01665579,
				-0.49394137, 1.37110953, 0.09031659,
				-0.00033467, -0.00103746, 0.91946965
			]
		).reshape(3, 3)
		
	sRGB = np.array(
			[
				2.52193473, -1.1370239, -0.38491083,
				-0.27547943, 1.36982898, -0.09434955,
				-0.01598287, -0.14778923, 1.1637721
			]
		).reshape(3, 3)
		
	sRGBinv = np.array(
			[
				0.43957568, 0.38391259, 0.17651173,
				0.08960038, 0.81471415, 0.09568546,
				0.01741548, 0.10873435, 0.87385017
			]
		).reshape(3, 3)
		
	aRGB = np.array(
			[
				1.72502307, -0.4228857, -0.30213736,
				-0.27547943, 1.36982898, -0.09434955,
				-0.02666425, -0.08532111, 1.11198537
			]
		).reshape(3, 3)
		
	aRGBinv = np.array(
			[
				0.61468318, 0.20122762, 0.1840892,
				0.12529321, 0.77491365, 0.09979314,
				0.02435304, 0.06428329, 0.91136367
			]
		).reshape(3, 3)
	



if __name__ == "__main__" :
	if not sys.argv: print('Use -t to test!')

	if sys.argv[1] == '-t' :
		print('Open openlut.py and scroll down to the end to see the code that\'s working!')
		#Open any format image. Try it with exr/dpx/anything!
		img = ColMap.open('testpath/test.exr') #Opens a test image 'test.exr', creating a ColMap object, automatically using the best image backend available to load the image at the correct bit depth.

		'''
		Gamma has gamma functions like Gamma.sRGB, called by value like Gamma.sRGB(val). All take one argument, the value (x), and returns the transformed value. Color doesn't matter for gamma.
		TransMat has matrices, in 3x3 numpy array form. All are relative to ACES, with direction aptly named. So, TransMat.XYZ is a matrix from ACES --> XYZ, while TransMat.XYZinv goes from XYZ --> ACES. All use/are converted to the D65 illuminant, for consistency sake.
		'''
	
		#Gamma Functions: sRGB --> Linear.
		gFunc = Gamma(Gamma.sRGBinv) #A Gamma Transform object using the sRGB-->Linear gamma formula. Apply to ColMaps!
		gFuncManualsRGB = Gamma(lambda val: ((val + 0.055) / 1.055) ** 2.4 if val > 0.04045 else val / 12.92) #It's generic - specify any gamma function, even inline with a lambda!
	
		#LUT from Function: sRGB --> Linear
		oLut = LUT.lutFunc(Gamma.sRGBinv) #A LUT Transform object, created from a gamma function. Size is 16384 by default. LUTs are faster!
		oLut.save('testpath/sRGB-->Lin.cube') #Saves the LUT to a format inferred from the extension. cube only for now!

		#Opening LUTs from .cube files.
		lut = LUT.open('testpath/sRGB-->Lin.cube') #Opens the lut we just made into a different LUT object.
		lut.resized(17).save('testpath/sRGB-->Lin_tiny.cube') #Resizes the LUT, then saves it again to a much smaller file!
	
		#Matrix Transformations
		simpleMat = TransMat(TransMat.sRGBinv) #A Matrix Transform (TransMat) object, created from a color transform matrix for gamut transformations! This one is sRGB --> ACES.
		mat = TransMat(TransMat.sRGBinv, TransMat.XYZ, TransMat.XYZinv, TransMat.aRGB) * TransMat.aRGBinv
		#Indeed, specify many matrices which auto-multiply into a single one! You can also combine them after, with simple multiplication.
	
		#Applying and saving.
		img.apply(gFunc).save('testpath/openlut_gammafunc.png') #save saves an image using the appropriate image backend, based on the extension.
		img.apply(lut).save('testpath/openlut_lut-lin-16384.png') #apply applies any color transformation object that inherits from Transform - LUT, Gamma, TransMat, etc., or make your own! It's easy ;) .
		img.apply(lut.resized(17)).save('testpath/openlut_lut-lin-17.png') #Why so small? Because spline interpolation automatically turns on. It's identical to the larger LUT!
		img.apply(mat).save('testpath/openlut_mat.png') #Applies the gamut transformation.

		#As a proof of concept, here's a long list of transformations that should, in sum, do nothing :) :

		img.apply(lut).apply(LUT.lutFunc(Gamma.sRGB)).apply(mat).apply(~mat).save('testpath/openlut_noop.png') #~mat is the inverse of mat. Easily undo the gamut operation!
	
		#Format Test: All output images are in Linear ACES.
		tImg = img.apply(mat)
		tImg.save('testpath/output.exr')
		tImg.save('testpath/output.dpx')
		tImg.save('testpath/output.png')
		tImg.save('testpath/output.jpg')
		tImg.save('testpath/output.tif') #All sorts of formats work! Bit depth is 16, unless you say something else.
	
		#Compression is impossible right now - wand is being difficult.
		#Keep in mind, values are clipped from 0 to 1 when done. Scary transforms can make this an issue!
	
		#Color management is simple: openlut doesn't touch your data, unless you tell it to with a Transform. So, the data that goes in, goes out, unless a Transform was applied.
