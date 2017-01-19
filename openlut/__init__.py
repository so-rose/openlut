#Set it up so that the users don't see the files containing the classes.
from .Transform import Transform
from .ColMap import ColMap
from .LUT import LUT
from .Func import Func
from .ColMat import ColMat
from .Viewer import Viewer

__all__ = ['ColMap', 'Transform', 'LUT', 'Func', 'ColMat', 'Viewer', 'gamma', 'gamut']

