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
LIBS_CV = /usr/local/lib/libopencv_calib3d.so /usr/local/lib/libopencv_contrib.so /usr/local/lib/libopencv_core.so /usr/local/lib/libopencv_features2d.so /usr/local/lib/libopencv_flann.so /usr/local/lib/libopencv_gpu.so /usr/local/lib/libopencv_highgui.so /usr/local/lib/libopencv_imgproc.so /usr/local/lib/libopencv_legacy.so /usr/local/lib/libopencv_ml.so /usr/local/lib/libopencv_nonfree.so /usr/local/lib/libopencv_objdetect.so /usr/local/lib/libopencv_ocl.so /usr/local/lib/libopencv_photo.so /usr/local/lib/libopencv_stitching.so /usr/local/lib/libopencv_superres.so /usr/local/lib/libopencv_ts.a /usr/local/lib/libopencv_video.so /usr/local/lib/libopencv_videostab.so /usr/local/cuda-6.0/lib64/libcufft.so /usr/local/cuda-6.0/lib64/libnpps.so /usr/local/cuda-6.0/lib64/libnppi.so /usr/local/cuda-6.0/lib64/libnppc.so /usr/local/cuda-6.0/lib64/libcudart.so /usr/lib/x86_64-linux-gnu/libXext.so /usr/lib/x86_64-linux-gnu/libX11.so /usr/lib/x86_64-linux-gnu/libICE.so /usr/lib/x86_64-linux-gnu/libSM.so /usr/lib/x86_64-linux-gnu/libGL.so /usr/lib/x86_64-linux-gnu/libGLU.so -lrt -lpthread -lm -ldl

# Caffe Libs
# LIBS_CAFFE = -lcaffe
# CAFFE_INCLUDE = /home/sudip/caffe/distribute/include
#

# Google Libs
LIBS_PROTOBUF = -lprotobuf -lglog -lleveldb -lsnappy

# Targets
EXEC=GpuPostProcessor
SOURCES= $(wildcard *.cpp)
INCLUDES= $(wildcard include/*.h*)
HEADERS= include
OBJECTS= $(SOURCES:.cpp=.o)
LFLAGS= $(BOOSTLFLAGS) $(FFMPEGLFLAGS) -I$(PYTHON_INCLUDE) -L/usr/local/lib -I. -I/usr/local/lib/python2.7/dist-packages/numpy/core/include
LIBS= $(BOOSTLIBS) $(FFMPEGLIBS) $(PYTHON_LIBS) $(LIBS_CV) $(LIBS_PROTOBUF)
SHAREDLIB= $(EXEC).so

#CFLAGS:= -Wall -ggdb -I$(HEADERS) -DDEBUG_BUILD -fPIC
CFLAGS:= -O3 -Wall -ggdb -I$(HEADERS) -fPIC

all: $(EXEC)
MAIN=GpuPostProcessor

$(MAIN): $(OBJECTS) $(SHAREDLIB)
	$(CC) $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJECTS) $(LIBS) $(LFLAGS)
$(SHAREDLIB): $(OBJECTS)
	g++ -shared -Wl,--export-dynamic $(OBJECTS) -L/usr/lib/python$(PYTHON_VERSION)/config -L/usr/local/lib -lpython$(PYTHON_VERSION) $(LIBS) -o $(MAIN).so

%.o: %.cpp
	$(CC) $(CFLAGS) $(LFLAGS) $(LIBS) -c $<  -o $@

clean:
	$(RM) *.o *.so *~ $(MAIN)
