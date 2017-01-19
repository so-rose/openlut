import abc

import numpy as np

class Transform :
	def spSeq(seq, outLen) :
		"""
		Utility function for splitting a sequence into equal parts, for multithreading.
		"""
		perfSep = (1/outLen) * len(seq)
		return list(filter(len, [seq[round(perfSep * i):round(perfSep * (i + 1))] for i in range(len(seq))])) if len(seq) > 1 else seq
		
	@abc.abstractmethod
	def sample(self, fSeq) :
		"""
		Samples the Transformation.
		"""
