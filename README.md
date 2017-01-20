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
Simply use pip: `sudo pip3 install openlut` (pip3 denotes that you must use a Python 3 version of pip). Keep in mind, there are some external dependencies:
* **Python 3.5**: This is Python; you need Python.
* **gcc**: This is needed to compile the C++ extensions.
* **pybind11**: This is a library needed to link the C++ extension into Python. pip version is being difficult...
* **imagemagick**: For all file IO. It's not like I was gonna write that myself :) .

*If it's breaking, try running `sudo pip3 install -U pip setuptools`. Sometimes they are out of date.*

Installing Dependencies
-----
Not Difficult, I promise!

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
