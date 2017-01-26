#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/functional.h>
//~ #include <pybind11/eigen.h>

//~ #include <Eigen/LU>

#include <iostream>
#include <cmath>

//~ #include "samplers.h"

//~ #define EPSILON 0.0001

namespace py = pybind11;
using namespace std;



//Gamma functions, ported to C++ for efficiency.

float lin(float x) { return x; }
float sRGB(float x) { return x > 0.0031308 ? (( 1.055 * pow(x, (1.0f / 2.4)) ) - 0.055) : x * 12.92; }
float sRGBinv(float x) { return x > 0.04045 ? pow(( (x + 0.055) / 1.055 ),  2.4) : x / 12.92; }
float Rec709(float x) { return x >= 0.018 ? 1.099 * pow(x, 0.45) - 0.099 : 4.5 * x; }
float ReinhardHDR(float x) { return x / (1.0 + x); }
float sLog(float x) { return (0.432699 * log10(x + 0.037584) + 0.616596) + 0.03; }
float sLog2(float x) { return ( 0.432699 * log10( (155.0 * x) / 219.0 + 0.037584) + 0.616596 ) + 0.03; }
float DanLog(float x) { return x > 0.1496582 ? (pow(10.0, ((x - 0.385537) / 0.2471896)) - 0.071272) / 3.555556 : (x - 0.092809) / 5.367655; }

//gam lets the user pass in any 1D array, any one-arg C++ function, and get a result. It's multithreaded, vectorized, etc. .
py::array_t<float> gam(py::array_t<float> arr, const std::function<float(float)> &g_func) {
	py::buffer_info bufIn = arr.request();
	
	//To use with an image, MAKE SURE to flatten the 3D array to a 1D array, then back out to a 3D array after.
	if (bufIn.ndim == 1) {
		//Make numpy allocate the buffer.
		auto result = py::array_t<float>(bufIn.size);
		
		//Get the pointers that we can manipulate from C++.
		auto bufOut = result.request();
		
		float 	*ptrIn = (float *) bufIn.ptr,
				*ptrOut = (float *) bufOut.ptr;
		
		//The reason for all this bullshit as opposed to vectorizing is this pragma!!!
		#pragma omp parallel for
		for (size_t i = 0; i < bufIn.shape[0]; i++) {
			//~ std::cout << g_func(ptrIn[i]) << std::endl;
			ptrOut[i] = g_func(ptrIn[i]);
		}
		
		return result;
	}
}


//lut1d takes a flattened image array and a flattened 1D array, and returns a linearly interpolated result.
py::array_t<float> lut1dlin(py::array_t<float> img, py::array_t<float> lut, float lBound, float hBound) {
	py::buffer_info bufImg = img.request(), bufLUT = lut.request();
	
	//To use with an image, MAKE SURE to flatten the 3D array to a 1D array, then back out to a 3D array after.
	if (bufImg.ndim == 1 && bufLUT.ndim == 1) {
		//Make numpy allocate the buffer of the new array.
		auto result = py::array_t<float>(bufImg.size);
		
		//Get the bufOut pointers that we can manipulate from C++.
		auto bufOut = result.request();
		
		float 	*ptrImg = (float *) bufImg.ptr,
				*ptrLUT = (float *) bufLUT.ptr,
				*ptrOut = (float *) bufOut.ptr;
		
		//Iterate over flat array. Each value gets scaled according to the LUT.
		#pragma omp parallel for
		for (size_t i = 0; i < bufImg.shape[0]; i++) {
			//~ std::cout << g_func(ptrImg[i]) << std::endl;
			//~ std::cout << g_func(ptrImg[i]) << std::endl;
			
			float val = ptrImg[i];
			
			if (val <= lBound) { ptrOut[i] = ptrLUT[0]; continue; }
			else if (val >= hBound) { ptrOut[i] = ptrLUT[bufLUT.shape[0] - 1]; continue; } //Some simple clipping. So it's safe to index.
			
			float lutVal = val * bufLUT.shape[0]; //Need the value in relation to LUT indices.
			//Essentially, we're gonna index by this above with simple math.
			
			// Linear Interpolation: y = y0 + (x - x0) * ( (y1 - y0) / (x1 - x0) )
			// See https://en.wikipedia.org/wiki/Linear_interpolation#Linear_interpolation_between_two_known_points .
			// (x0, y0) is lower point, (x, y) is higher point.
			int x0 = (int)floor(lutVal);
			int x1 = (int)ceil(lutVal); //Internet says this is safe. Yay internet...
			
			float y0 = ptrLUT[x0];
			float y1 = ptrLUT[x1];
			
			// (y1 - y0) is divided by the result of (float)(x1 - x0) - but no need to write it; a ceil'ed minus a floor'ed int is just 1.
			ptrOut[i] = y0 + (lutVal - (float)x0) * ( (y1 - y0) );
		}
		
		return result;
	}
}


//matr takes a flattened image array and a flattened 3x3 matrix.
py::array_t<float> matr(py::array_t<float> img, py::array_t<float> mat) {
	py::buffer_info bufImg = img.request(), bufMat = mat.request();
	
	//To use with an image, MAKE SURE to flatten the 3D array to a 1D array, then back out to a 3D array after.
	if (bufImg.ndim == 1 && bufMat.ndim == 1) {
		//Make numpy allocate the buffer of the new array.
		auto result = py::array_t<float>(bufImg.size);
		
		//Get the bufOut pointers that we can manipulate from C++.
		auto bufOut = result.request();
		
		float 	*ptrImg = (float *) bufImg.ptr,
				*ptrMat = (float *) bufMat.ptr,
				*ptrOut = (float *) bufOut.ptr;
		
		//We flatly (parallelly) iterate by threes - r, g, b. To do matrix math. Yay!
		#pragma omp parallel for
		for (size_t i = 0; i < bufImg.shape[0]; i+=3) {
			//~ std::cout << g_func(ptrImg[i]) << std::endl;
			//~ std::cout << g_func(ptrImg[i]) << std::endl;
			
			/* Remember: We're dealing with a flattened matrix here. Indices for ptrMat:
			*	0	1	2
			*	3	4	5
			* 	6	7	8
			*/
			
			float	r = ptrImg[i],
					g = ptrImg[i + 1],
					b = ptrImg[i + 2];
			
			ptrOut[i] = r * ptrMat[0] + g * ptrMat[1] + b * ptrMat[2]; //Red
			ptrOut[i + 1] = r * ptrMat[3] + g * ptrMat[4] + b * ptrMat[5]; //Green
			ptrOut[i + 2] = r * ptrMat[6] + g * ptrMat[7] + b * ptrMat[8]; //Blue
		}
		
		return result;
	}
}

//grey_to_rgb takes a flattened greyscale image array and outputs a flattened numpy image array.
py::array_t<float> grey_to_rgb(py::array_t<float> arr) {
	py::buffer_info bufIn = arr.request();
	
	//To use with an image, MAKE SURE to flatten the 3D array to a 1D array, then back out to a 3D array after.
	if (bufIn.ndim == 1) {
		//Make numpy allocate the buffer.
		auto result = py::array_t<float>(bufIn.size * 3); //Size is multiplied by 3 - we're outputting RGB!
		
		//Get the pointers that we can manipulate from C++.
		auto bufOut = result.request();
		
		float 	*ptrIn = (float *) bufIn.ptr,
				*ptrOut = (float *) bufOut.ptr;
		
		//The reason for all this bullshit as opposed to vectorizing is this pragma!!!
		#pragma omp parallel for
		for (size_t i = 0; i < bufOut.shape[0]; i+=3) {
			float val = ptrIn[(i+1)/3 - 1]; //Little bit of indexing math to get the value; remember we're skipping by threes.
			
			ptrOut[i] = val;
			ptrOut[i + 1] = val;
			ptrOut[i + 2] = val;
		}
		
		return result;
	}
}




PYBIND11_PLUGIN(olOpt) {
	py::module mod("olOpt", "Optimized C++ functions for openlut.");
	
	mod.def(	"gam",
				&gam,
				"Apply any one-argument C++ function to a flattened numpy array; vectorized & parallel.",
				py::arg("arr"),
				py::arg("g_func")
	);
	
	mod.def(	"matr",
				&matr,
				"Apply any flattened color matrix to a flattened numpy image array; vectorized & parallel.",
				py::arg("img"),
				py::arg("mat")
	);
	
	mod.def(	"grey_to_rgb",
				&grey_to_rgb,
				"Takes a flattened 2D greyscale image array and outputs a flattened 3D numpy image array.",
				py::arg("arr")
	);
	
	mod.def(	"lut1dlin",
				&lut1dlin,
				"Apply any 1D LUT to a flattened numpy image array; vectorized & parallel.",
				py::arg("img"),
				py::arg("lut"),
				py::arg("lBound"),
				py::arg("hBound")
	);
	
	
	
	//Simple Gamma Functions
	
	mod.def(	"lin",
				&lin,
				"The linear gamma function.",
				py::arg("x")
	);
	
	mod.def(	"sRGB",
				&sRGB,
				"The lin --> sRGB gamma function.",
				py::arg("x")
	);
	
	mod.def(	"sRGBinv",
				&sRGBinv,
				"The sRGB --> lin function.",
				py::arg("x")
	);
	
	mod.def(	"Rec709",
				&Rec709,
				"The lin --> Rec709 function.",
				py::arg("x")
	);
	
	mod.def(	"ReinhardHDR",
				&ReinhardHDR,
				"The lin --> ReinhardHDR function.",
				py::arg("x")
	);
	
	mod.def(	"sLog",
				&sLog,
				"The lin --> sLog function.",
				py::arg("x")
	);
	
	mod.def(	"sLog2",
				&sLog2,
				"The lin --> sLog2 function.",
				py::arg("x")
	);
	
	mod.def(	"DanLog",
				&DanLog,
				"The lin --> DanLog function.",
				py::arg("x")
	);
	
	return mod.ptr();
}
