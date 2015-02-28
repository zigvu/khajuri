# Compiler
CC:= g++

# FFMPEG libraries
FFMPEGLFLAGS:= $(shell pkg-config --cflags libavformat libavcodec libswscale libavutil sdl) 
FFMPEGLIBS:= $(shell pkg-config --libs libavformat libavcodec libswscale libavutil sdl) -lm

#Python
PYTHON_VERSION = 2.7
PYTHON_INCLUDE = /usr/include/python$(PYTHON_VERSION)
PYTHON_LIBS= -lpython2.7

# Boost libraries
BOOSTLFLAGS= -I/usr/include/boost
BOOSTLIBS= -lboost_thread -lboost_system -lboost_python

# Open CV Libs
LIBS_CV = -lopencv_highgui -lopencv_imgproc -lopencv_core # opencv-2.0

# Caffe Libs
# LIBS_CAFFE = -lcaffe
# CAFFE_INCLUDE = /home/sudip/caffe/distribute/include
#

# Google Libs
LIBS_PROTOBUF = -lprotobuf -lglog -lleveldb -lsnappy -llmdb

# Targets
EXEC= VideoReader
SOURCES= $(filter-out caffe.pb.cpp, $(wildcard *.cpp))
INCLUDES= $(filter-out include/caffe.pb.h, $(wildcard include/*.h))
HEADERS= include
OBJECTS= $(SOURCES:.cpp=.o) caffe.pb.o
LFLAGS= $(BOOSTLFLAGS) $(FFMPEGLFLAGS) -I$(PYTHON_INCLUDE) -L/usr/local/lib -I.
LIBS= $(BOOSTLIBS) $(FFMPEGLIBS) $(PYTHON_LIBS) $(LIBS_CV) $(LIBS_PROTOBUF)
SHAREDLIB= $(EXEC).so

CFLAGS:= -Wall -ggdb -I$(HEADERS) -DDEBUG_BUILD -fPIC
#CFLAGS:= -O3 -Wall -ggdb -I$(HEADERS) -fPIC

all: $(EXEC)
MAIN= VideoReader

$(MAIN): protoc $(OBJECTS) $(SHAREDLIB)
	$(CC) $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJECTS) $(LIBS) $(LFLAGS)

$(SHAREDLIB): $(OBJECTS)
	g++ -shared -Wl,--export-dynamic $(OBJECTS) -L/usr/lib/python$(PYTHON_VERSION)/config -L/usr/local/lib -lpython$(PYTHON_VERSION) $(LIBS) -o $(MAIN).so

%.o: %.cpp protoc
	$(CC) $(CFLAGS) $(LFLAGS) $(LIBS) -c $<  -o $@

cleanobj:
	$(RM) *.o *~ *.so

clean:
	$(RM) *.o *~ $(MAIN) $(MAIN).so caffe.pb.cpp include/caffe.pb.h

protoc: caffe.proto
	protoc caffe.proto --cpp_out=.	
	mv caffe.pb.cc caffe.pb.cpp
	mv caffe.pb.h include/caffe.pb.h
	$(CC) $(CFLAGS) $(LFLAGS) $(LIBS) -c caffe.pb.cpp

caffe.pb.o: protoc
