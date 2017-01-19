import math

import numpy as np

from .lib import olOpt as olo

#Static Gamma Functions, borrowed from olo.
#inv goes from space to lin.

lin = olo.lin
sRGB = olo.sRGB
sRGBinv = olo.sRGBinv
Rec709 = olo.Rec709
ReinhardHDR = olo.ReinhardHDR
sLog = olo.sLog
sLog2 = olo.sLog2
DanLog = olo.DanLog

class PGamma :
	'''
	Static class containing python versions of the C++ gamma functions.
	'''
	
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
