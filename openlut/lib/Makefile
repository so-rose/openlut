#Macros
SHELL=/bin/sh

FILES = olOpt.cpp
#~ LIBS = openimageio

CXXFLAGS = -O3 -shared -Wall -std=gnu++14 -fopenmp -fPIC
PYTHONFLAGS = $(shell python3-config --cflags) $(shell python3-config --ldflags)
CXX = g++

LIBS = 

DATE = $(shell date)

#Main Rules

all: olOpt

clean:
	-rm -f *.so
	
#~ clean-deps:
#~ 	-rm -rf libs
	
#~ clean-all: clean clean-deps
	
install:
	@echo "Not Yet Implemented"
	
debug:
	

#Executables

olOpt: ${FILES}
	${CXX} -o $@.so ${FILES} ${CXXFLAGS} ${LIBS} ${PYTHONFLAGS}
	@echo "Successfully compiled at" ${DATE}
