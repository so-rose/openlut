import multiprocessing as mp
from functools import reduce
import types

import numpy as np

MOD_SCIPY = False
try :
	from scipy.interpolate import splrep, splev
	MOD_SCIPY = True
except :
	pass

from .Transform import Transform
from .lib import olOpt as olo

class LUT(Transform) :
	def __init__(self, dims = 1, size = 16384, title = "openlut_LUT", iRange = (0.0, 1.0)) :	
		'''
		Create an identity LUT with given dimensions (1 or 3), size, and title.
		'''	
		if dims != 1 and dims != 3: raise ValueError("Dimensions must be 1 or 3!")
		
		self.title = title #The title.
		self.size = size #The size. 1D LUTs: size numbers. 3D LUTs: size x size x size numbers.
		self.range = iRange #The input range - creates data or legal LUTs. Should work fine, but untested.
		self.dims = dims #The dimensions. 1 or 3; others aren't accepted.
		self.ID = np.linspace(self.range[0], self.range[1], self.size, dtype=np.float32) #Read Only.
		
		if dims == 1 :
			self.array = np.linspace(self.range[0], self.range[1], self.size, dtype=np.float32) #Size number of floats.
		elif dims == 3 :
			print("3D LUT Not Implemented!")
			#~ self.array = np.linspace(self.range[0], self.range[1], self.size**3).reshape(self.size, self.size, self.size) #Should make an identity size x size x size array.
		
	def lutFunc(func, size = 16384, dims = 1, title="openlut_FuncGen", iRange = (0.0, 1.0)) :
		'''
		Creates a LUT from a simple function.
		'''
		if dims == 1 :
			lut = LUT(dims=dims, size=size, title=title, iRange=iRange)
			
			#Use fast function sampling if the function is a C++ function.
			vFunc = lambda arr: olo.gam(arr, func) if isinstance(func, types.BuiltinFunctionType) else np.vectorize(func, otypes=[np.float32])
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
			
	def lutMapping(idArr, mapArr, title="Mapped_Array") :
		'''
		Creates a 1D LUT from a nonlinear mapping. Elements must be in range [0, 1].
		'''
		return LUT.lutArray(splev(np.linspace(0, 1, num=len(idArr)), splrep(idArr, mapArr)))
		
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
		'''
		Return the LUT, resized to newSize.
		
		1D LUTs: If the new size is lower, we use Linear interpolation. If the new size is higher, we use Spline interpolation.
		* If the current size is too low, use spline regardless.
		'''
		if newSize == self.size: return self
			
		fac = newSize / self.size
		
		useSpl = self.size < newSize #If the new size is lower, we use Linear interpolation. If the new size is higher, we use Spline interpolation.
		if self.size < 128: useSpl = True #If the current size is too low, use spline regardless.
		
		if self.dims == 1 :
			newID = np.linspace(self.range[0], self.range[1], newSize)
			return LUT.lutArray(self.sample(newID, spl=useSpl), title="Resized to {0}".format(newSize))
		if self.dims == 3 :
			print("3D LUT Not Implemented")
			
	def inverted(self) :
		'''
		Return the inverse LUT.
		'''
		return LUT.lutArray(splev(np.linspace(self.range[0], self.range[1], num=self.size), splrep(self.array, np.linspace(self.range[0], self.range[1], num=self.size))))
	
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
