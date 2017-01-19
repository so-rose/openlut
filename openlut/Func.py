import multiprocessing as mp
import types
from functools import reduce

import numpy as np

from .Transform import Transform
from .lib import olOpt as olo

class Func(Transform) :
	def __init__(self, func) :
		self.func = func
		
	#Func Methods
	def __gamma(q, cpu, f, spSeq) :
		q.put( (cpu, f(spSeq)) )
	
	def sample(self, fSeq) :
		fSeq = np.array(fSeq, dtype=np.float32) #Just some type assurances.
		
		# Any float-returning C++ functions can be threaded with olo.gam(), but because of GIL, it won't work with Python functions.
		if isinstance(self.func, types.BuiltinFunctionType) :
			# \/ Just olo.gam, except fSeq is flattened to a 1D array, processed flat, then shaped back into a 3D array on the fly.
			return olo.gam(fSeq.reshape(reduce(lambda a, b: a*b, fSeq.shape)), self.func).reshape(fSeq.shape) #OpenMP vectorized C++ motherfuckery!
		else :
			#We always have the slow af fallback.
			fVec = np.vectorize(self.func)
			
			out = []
			q = mp.Queue()
			splt = Transform.spSeq(fSeq, mp.cpu_count())
			for cpu in range(mp.cpu_count()) :
				p = mp.Process(target=Func.__gamma, args=(q, cpu, fVec, splt[cpu]))
				p.start()
				
			for num in range(len(splt)) :
				out.append(q.get())
				
			return np.concatenate([seq[1] for seq in sorted(out, key=lambda seq: seq[0])], axis=0) if len(fSeq) > 1 else self.func(fSeq[0])
			
			#~ return fVec(fSeq) if len(fSeq) > 1 else self.func(fSeq[0])
		
