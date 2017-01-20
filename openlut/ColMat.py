import multiprocessing as mp
from functools import reduce
import operator as oper

import numpy as np
#~ import numba

from .Transform import Transform

class ColMat(Transform) :
	def __init__(self, *mats) :
		'''
		Initializes a combined 3x3 Transformation Matrix from any number of input matrices. These may be numpy arrays, matrices,
		other ColMats, or any combination thereof.
		'''
		if len(mats) == 1 :
			mat = mats[0]
			
			if isinstance(mat, ColMat) :
				self.mat = mat.mat #Support a copy constructor.
			else :
				self.mat = np.array(mat) #Simply set self.mat with the numpy array version of the mat.
		elif len(mats) > 1 :
			self.mat = ColMat.__mats(*[ColMat(mat) for mat in mats]).mat
		elif not mats :
			self.mat = np.identity(3)
		
	def __mats(*inMats) :
		'''
		Initialize a combined Transform matrix from several input ColMats.
		'''
		return ColMat(reduce(ColMat.__mul__, reversed(inMats))) #Works because multiply is actually non-commutative dot.
		#This is why we reverse inMats.
		
	#~ @numba.jit(nopython=True)
	def __optDot(img, mat, shp, out) :
		'''
		Dots the matrix with each tuple of colors in the img.

		img: Numpy array of shape (height, width, 3).
		mat: The 3x3 numpy array representing the color transform matrix.
		shp: The shape of the image.
		out: the output list. Built mutably for numba's sake.
		'''
		shaped = img.reshape((shp[0] * shp[1], shp[2])) #Flatten to 2D array for iteration over colors.
		i = 0
		while i < shp[0] * shp[1] :
			res = np.dot(mat, shaped[i])
			out[i] = res
			i += 1
			
	def __applMat(q, cpu, shp, mat, img3D) :
		out = np.zeros((shp[0] * shp[1], shp[2]))
		ColMat.__optDot(img3D, mat, shp, out)
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
				p = mp.Process(target=ColMat.__applMat, args=(q, cpu, np.shape(splt[cpu]), self.mat, splt[cpu]))
				p.start()
				
			for num in range(len(splt)) :
				out.append(q.get())
				
			return np.concatenate([seq[1] for seq in sorted(out, key=lambda seq: seq[0])], axis=0)
			
			#~ out = np.zeros((shp[0] * shp[1], shp[2]))
			#~ ColMat.__optDot(fSeq, self.mat, shp, out)
			#~ return out.reshape(shp)
			
			#~ return np.array([self.mat.dot(col) for col in fSeq.reshape(shp[0] * shp[1], shp[2])]).reshape(shp)
			
			#~ p = mp.Pool(mp.cpu_count())
			#~ return np.array(list(map(self.mat.dot, fSeq.reshape(shp[0] * shp[1], shp[2])))).reshape(shp)
		#~ return fSeq.dot(self.mat)
		
	def inv(obj) :
		if isinstance(obj, ColMat) : #Works on any ColMat object - including self.
			return ColMat(np.linalg.inv(obj.mat))
		else : #Works on raw numpy arrays as well.
			return np.linalg.inv(obj)
		
	def transpose(self) :
		return ColMat(np.transpose(self.mat))
		
	#Overloading
	def __mul__(self, other) :
		'''
		* implements matrix multiplication.
		'''
		if isinstance(other, ColMat) :
			return ColMat(self.mat.dot(other.mat))
		elif isinstance(other, float) or isinstance(other, int) :
			return ColMat(np.multiply(self.mat, other))
		elif isinstance(other, np.ndarray) or isinstance(other, np.matrixlib.defmatrix.matrix) :
			return ColMat(self.mat.dot(np.array(other)))
		else :
			raise ValueError('Invalid multiplication arguments!')
			
	__rmul__ = __mul__
	
	def __add__(self, other) :
		if isinstance(other, ColMat) :
			return ColMat(self.mat + other.mat)
		elif isinstance(other, np.ndarray) or isinstance(other, np.matrixlib.defmatrix.matrix) :
			return ColMat(self.mat + np.array(other))
		else :
			raise ValueError('Invalid addition arguments!')
			
	__radd__ = __add__
	
	def __pow__(self, other) :
		'''
		** implements direct multiplication. You usually don't want this.
		'''
		if isinstance(other, ColMat) :
			return ColMat(self.mat * other.mat)
		elif isinstance(other, float) or isinstance(other, int) :
			return ColMat(np.multiply(self.mat, other))
		elif isinstance(other, np.ndarray) or isinstance(other, np.matrixlib.defmatrix.matrix) :
			return ColMat(self.mat * np.array(other))
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
		return "\nColMat (\n{0}  )\n".format(str(self.mat))
		

