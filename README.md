# openlut

## Open-source tools for practical color management.

What is it?
-----
openlut is, at its core, a color management library, accessible from **Python 3.5+**. It's built on my own color pipeline needs, which includes managing
Lookup Tables, Gamma/Gamut functions/matrices, applying color transformations, etc. .

openlut is also a tool. Included soon will be a command line utility letting you perform complex color transformations from the comfort of
your console. In all cases, interactive usage from a Python console is easy.

I wanted it to cover this niche simply and consistently, something color management often isn't! Take a look; hopefully you'll agree :) !


What About OpenColorIO? Why does this exist?
------
OpenColorIO is a wonderful library, but seems geared towards managing the complexity of many larger applications in a greater pipeline.
openlut is more simple; it doesn't care about the big picture - you just do consistent operations on images. openlut also has tools to deal
with these building blocks, unlike OCIO - resizing LUTs, etc. .

Indeed, OCIO is just a system these basic operations using LUTs - in somewhat unintuitive ways, in my opinion. You could setup a similar system
using openlut's toolkit.


Installation
-----
I'll put it on pip eventually (when I figure out how!). For now, just download the repository.

To run openlut.py, first make sure you have the *Dependencies*. To run the test code at the bottom (make sure openlut is in the same
directory as testpath; it needs to load test.exr), you can then run:

`python3 main.py -t`

To use in your code, simply `import` the module at the top of your file.


Dependencies
-----
There are some dependencies that you must get. Keep in mind that it's **Python 3.X** *only*; all dependencies must be their 3.X versions.

### Getting python3 and pip3
If you're on a **Mac**, run this to get python3 and pip3: `brew install python3; curl https://bootstrap.pypa.io/get-pip.py | python3`
If you're on **Linux**, you should already have python3 and pip3 - otherwise see your distribution repositories.

### Dependency Installation
Run this to get all deps: `sudo pip3 install numpy wand numba scipy`

Basic Library Usage
-----
To represent images, use a **ColMap** object. This handles IO to/from all ImageMagick supported formats (**including EXR and DPX**),
as well as storing the image data.

Use any child of the **Transform** class to do a color transform on a ColMap, using ColMap's `apply(Transform)` method.

The **Transform** objects themselves have plenty of features - like LUT, with `open()`, `save()`, and `resize()` methods, or TransMat with auto-combining
input matrices, or automatic spline-based interpolation of very small 1D LUTs - to make them helpful in and of themselves!


The best way to demonstrate this, I think, is to show some test code: (run python3 openlut.py -t to see it work)

```python
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

#Color management of openlut itself is simple: openlut doesn't touch your data, unless you tell it to with a Transform. So, the data that goes in, goes out, unless a Transform was applied.

```
