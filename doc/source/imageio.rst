Image IO
=================
This section deals with getting images in and out of openlut.

Introduction
----------------------------

Image IO in openlut happens via the ColMap module, which handles loading, transforming,
and saving images. As the name might suggest, a ColMap is a simple container storing RGB
data.

Internally, it uses a 32-bit numpy float array with an unenforced clipping range of [0, 1], of the
shape **(height, width, 3)**.

First, import the relevant code:

.. doctest::

	>>> import openlut as ol
	>>> from openlut import ColMap, Func, gamma
	
You can open an image on the disk with the :py:func:`~openlut.ColMap.open` method and
an image path:

.. doctest::

	>>> img = ColMap.open('../img_test/rock.exr')
	>>> ColMap.display('../img_test/rock.exr') #Display the image directly from a path.
	
The referenced image 'rock.exr' looks like this:

.. image:: ../images/rock.jpg

*The linear exr data has been transformed for correct web browser viewing. See the NOTE at the bottom.*
	
Saving that image is as easy as a call to :py:func:`~openlut.ColMap.save`, which infers
the output format directly from the extension:

.. doctest::

	>>> img.save('../img_test/saved_rock.dpx')
	
But now to the meat of it: Image transforms are trivial to apply to ColMaps because
of the :py:func:`~openlut.ColMap.apply` method! See :py:class:`~openlut.ColMap.Transform` for more.

.. doctest::
	
	>>> transform = Func(gamma.sRGB) #We'll be applying an sRGB function today.
	>>> img.apply(transform).show()
	
The transformed image looks like this:

.. image:: ../images/rock-transformed.jpg

*The linear exr data has been transformed for correct web browser viewing. See the NOTE at the bottom.*
	
There's a few elements at play here:

* We can plop **any subclass** of :py:class:`~openlut.Transform` into the :py:func:`~openlut.ColMap.apply` method.
* :py:class:`~openlut.Func` is one such class. In this case, we initialize it with openlut's builtin :py:const:`~openlut.gamma.sRGB` function.
* The :py:const:`~openlut.gamma.sRGB` function comes from the :py:mod:`~openlut.gamma` module, where you can find a wide variety of such functions.
* The :py:func:`~openlut.ColMap.show` method displays the image interactively, in an OpenGL viewer.

After applying a transform, you can . :py:func:`~openlut.ColMap.save` it perhaps, apply more transforms, etc. . But are the basics!
Take a look at the ColMap class documentation for more!


**IMPORTANT NOTE**: When loading/saving images, **openlut won't touch the raw image data**. This can be problematic, 
because most formats like jpg and png store their data already transformed by an sRGB gamma curve, making
your image as shown in openlut **look too bright**.

* You can undo this easily: Just apply an inverse sRGB LUT or Func.
* EXR is one of the only formats that won't touch your data, keeping it linear.

ColMap: Image IO
------------------------

.. automodule:: openlut.ColMap
    :members:
    :undoc-members:
    :show-inheritance:
