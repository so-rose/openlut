#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/functional.h>
//~ #include <pybind11/eigen.h>

//~ #include <Eigen/LU>

#include <iostream>
#include <cmath>

//~ #include "samplers.h"

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





PYBIND11_PLUGIN(olOpt) {
	py::module mod("olOpt", "Optimized C++ functions for openlut.");
	
	mod.def(	"gam",
				&gam,
				"The sRGB function, vectorized."
	);
	
	mod.def(	"lin",
				&lin,
				"The linear function."
	);
	
	mod.def(	"sRGB",
				&sRGB,
				"The sRGB function."
	);
	
	mod.def(	"sRGBinv",
				&sRGBinv,
				"The sRGBinv function."
	);
	
	mod.def(	"Rec709",
				&Rec709,
				"The Rec709 function."
	);
	
	mod.def(	"ReinhardHDR",
				&ReinhardHDR,
				"The ReinhardHDR function."
	);
	
	mod.def(	"sLog",
				&sLog,
				"The sLog function."
	);
	
	mod.def(	"sLog2",
				&sLog2,
				"The sLog2 function."
	);
	
	mod.def(	"DanLog",
				&DanLog,
				"The DanLog function."
	);
	
	return mod.ptr();
}
