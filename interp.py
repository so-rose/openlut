from functools import reduce
from imp import reload

import numpy as np
import openlut as ol
from openlut.lib.files import Log

img = ol.ColMap.open('img_test/rock.exr')
fSeq = img.rgbArr
lut = ol.LUT.lutFunc(ol.gamma.sRGB)
