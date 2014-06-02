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

# Targets
EXEC= VideoReader
SOURCES= $(wildcard *.cpp)
INCLUDES= $(wildcard include/*.h*)
HEADERS= include
OBJECTS= $(SOURCES:.cpp=.o)
LFLAGS= $(BOOSTLFLAGS) $(FFMPEGLFLAGS) -I$(PYTHON_INCLUDE)
LIBS= $(BOOSTLIBS) $(FFMPEGLIBS) $(PYTHON_LIBS) $(LIBS_CV)
SHAREDLIB= $(EXEC).so

#CFLAGS:= -Wall -ggdb -I$(HEADERS) -DDEBUG_BUILD -fPIC
CFLAGS:= -Wall -ggdb -I$(HEADERS) -fPIC

all: $(EXEC)
MAIN= VideoReader

$(MAIN): $(OBJECTS) $(SHAREDLIB)
	$(CC) $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJECTS) $(LIBS) $(LFLAGS)

$(SHAREDLIB): $(OBJECTS)
	g++ -shared -Wl,--export-dynamic $(OBJECTS) -L/usr/lib/python$(PYTHON_VERSION)/config -lpython$(PYTHON_VERSION) $(LIBS) -o $(MAIN).so

%.o: %.cpp
	$(CC) $(CFLAGS) $(LFLAGS) $(LIBS) -c $<  -o $@

cleanobj:
	$(RM) *.o *~ *.so

clean:
	$(RM) *.o *~ $(MAIN) $(MAIN).so
