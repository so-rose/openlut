# openlut

## Open-source tools for practical color management.

What is it?
-----
openlut is, at its core, a transform-focused color management library, accessible from **Python 3.5+**. It's built on my own color pipeline needs, which includes managing
Lookup Tables, Gamma/Gamut functions/matrices, applying color transformations, etc. .

openlut is also a practical tool. Included soon will be a command line utility letting you perform complex color transformations from the comfort of
your console. Included already is an OpenGL image viewer, which might grow in the future to play sequences.

I wanted it to cover this niche simply and consistently, with batteries included (a library of gamma functions and color gamut matrices).
Color management doesn't have to be so difficult!


What About OpenColorIO? Why does this exist?
------
OpenColorIO does amazing work - but mostly in the context of large applications, not-simple config files, and self-defined color space
(with the full range of int/float bit depth specifics, etc.)

openlut is all about images and the transforms on images. Everything happens in (0, 1) float space. Large emphasis is placed on managing the 
tools themselves as well - composing matrices, resizing LUTs, defining new gamma functions, etc. .

In many ways, OCIO is a system stringing basic operations together. I'd be perfectly plausible to write an OCIO alternative with openlut in the backend.


Installation
-----
Simply use pip: `sudo pip3 install openlut` (pip3 denotes that you must use a Python 3 version of pip). Keep in mind, there are some external dependencies:
* **Python 3.5**: This is Python; you need Python.
* **gcc**: This is needed to compile the C++ extensions.
* **pybind11**: This is a library needed to link the C++ extension into Python. pip version is being difficult...
* **imagemagick**: For all file IO. It's not like I was gonna write that myself :) .

*If it's breaking, try running `sudo pip3 install -U pip setuptools`. Sometimes they are out of date.*

Installing Compile Dependencies
-----
For the moment, I don't have a Mac wheel. Not Difficult, I promise!

On Debian/Ubuntu: `sudo apt-get install python3-pip gcc pybind11-dev libmagickwand-dev`
On Mac: `brew install python3 gcc pybind11 imagemagick`
* You will need Homebrew ( copy/paste a command from http://brew.sh/ ) and XCode Command Line Tools for gcc (it should prompt you to install this).
* Disclaimer - gcc took its sweet time compiling/installing on my old Mac...


Dependencies
-----
There are some dependencies that you must get. Keep in mind that it's **Python 3.X** *only*; all dependencies must be their 3.X versions.

### Getting python3 and pip3
If you're on a **Mac**, run this to get python3 and pip3: `brew install python3; curl https://bootstrap.pypa.io/get-pip.py | python3`
If you're on **Linux**, you should already have python3 and pip3 - otherwise see your distribution repositories.

### Dependency Installation
You need **Python 3.5**, **Pip**, a newer version (must support C++14) of **gcc**, and pybind11 in your `includes`. This is trivial on Debian/Ubuntu:
* `sudo apt-get install python3-pip 

Basic Library Usage
-----
To represent images, use a **ColMap** object. This handles IO to/from all ImageMagick supported formats (**including EXR and DPX**),
as well as storing the image data.

Use any child of the **Transform** class to do a color transform on a ColMap, using ColMap's `apply(Transform)` method.

The **Transform** objects themselves have plenty of features - like LUT, with `open()`, `save()`, and `resize()` methods, or TransMat with auto-combining
input matrices, or automatic spline-based interpolation of very small 1D LUTs - to make them helpful in and of themselves!


Take a look at the test code under tests for examples.
