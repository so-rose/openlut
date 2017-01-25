import multiprocessing as mp
from functools import reduce
import operator as oper

import numpy as np
#~ import numba

from .Transform import Transform
from .lib import olOpt as olo

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
			self.mat = ColMat._mats(*[ColMat(mat) for mat in mats]).mat
		elif not mats :
			self.mat = np.identity(3)
		
	def _mats(*inMats) :
		'''
		Initialize a combined Transform matrix from several input ColMats. Use constructor instead.
		'''
		return ColMat(reduce(ColMat.__mul__, reversed(inMats))) #Works because multiply is actually non-commutative dot.
		#This is why we reverse inMats.
	
	def sample(self, fSeq) :
		shp = np.shape(fSeq)
		if len(shp) == 1 :
			return self.mat.dot(fSeq)
		if len(shp) == 3 :
			#C++ based olo.matr replaces & sped up the operation by 50x with same output!!!
			return olo.matr(fSeq.reshape(reduce(lambda a, b: a*b, fSeq.shape)), self.mat.reshape(reduce(lambda a, b: a*b, self.mat.shape))).reshape(fSeq.shape)
		
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
		

