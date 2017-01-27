# openlut - OSS tools for practical color management.

[![build status](https://git.sofusrose.com/so-rose/openlut/badges/master/build.svg)](https://git.sofusrose.com/so-rose/openlut/commits/master)

**Main Dev Repo**: https://git.sofusrose.com/so-rose/openlut (GitLab)
**PyPi Package**: https://pypi.python.org/pypi/openlut

What is it?
-----
openlut is, at its core, a transform-focused **color management library**, accessible from **Python 3.5+**. It's built on my own color pipeline needs, which includes managing Lookup Tables, Gamma/Gamut functions/matrices, applying color transformations, etc. .

openlut is also a practical tool. Included soon will be a command line utility letting you perform complex color transformations from the comfort of your console. Included already is an OpenGL image viewer, which might grow in the future to play sequences.

I wanted it to cover this niche simply and consistently, with batteries included (a library of gamma functions and color gamut matrices).

Documentation
-----
Docs can be found at https://sofusrose.com/openlut. They're a work in progress for now (ColMap is 100% documented).

Installation
-----
1. **Get the dependencies!!!** The pip command will break without them.
    * **On Debian/Ubuntu**: `sudo apt-get install python3-pip gcc libmagickwand-dev`
    * **On Mac**: `brew install python3 gcc imagemagick`
    * **All**: Make sure **pip**, **setuptools**, and **wheel** are installed. `pip3 install -U pip setuptools wheel`. It can cause errors if they aren't.

2. Run `pip3 install openlut` *(possibly sudo)*. This step **relies** on the successful installation of deps:
    * **Python 3.5**: This is Python. You need Python.
    * **gcc**: This is needed to compile the C++ extension.
    * **imagemagick**: For all file IO. It's not like I was gonna write that myself :) .

*Linux: Ignore the AssertionError when building the wheel; it doesn't affect anything.*

Troubleshooting
-----
If python's installed but pip won't install, run `curl https://bootstrap.pypa.io/get-pip.py | python3`

No Windows support right now - it's the C++ module's fault.

Start an issue if something goes wrong with the library itself!

Misc. Systems need, generically:
* Python 3.5+
* Pip
* gcc (with c++14 and openmp support)


What About OpenColorIO? Why does this exist?
------
OpenColorIO does amazing work - but mostly in the context of large applications, not-simple config files, and self-defined color space
(with the full range of int/float bit depth specifics, etc.)

openlut is all about images and the transforms on images. Everything happens in (0, 1) float space. Large emphasis is placed on managing the 
tools themselves as well - composing matrices, resizing LUTs, defining new gamma functions, etc. .

In many ways, OCIO is a system stringing basic operations together. I'd be perfectly plausible to write an OCIO alternative with openlut in the backend.

I Wanna Contribute!
------
I'm honored! I could use help with:
* Feedback
* Gamma Transfer Functions: The more "batteries" are included, the better!
* D65 XYZ-referenced color matrices (gamut definitions): See above.
