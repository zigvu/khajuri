# Compiler
CC:= g++

# FFMPEG libraries
FFMPEGLFLAGS:= $(shell pkg-config --cflags libavformat libavcodec libswscale libavutil sdl) 
FFMPEGLIBS:= $(shell pkg-config --libs libavformat libavcodec libswscale libavutil sdl) -lm

# Boost libraries
BOOSTLFLAGS= -I/usr/include/boost
BOOSTLIBS= -lboost_thread -lboost_system

# Targets
EXEC= VideoReader
SOURCES= $(wildcard *.cpp)
INCLUDES= $(wildcard include/*.h*)
HEADERS= include
OBJECTS= $(SOURCES:.cpp=.o)
LFLAGS= $(BOOSTLFLAGS) $(FFMPEGLFLAGS)
LIBS= $(BOOSTLIBS) $(FFMPEGLIBS) 

CFLAGS:= -Wall -ggdb -I$(HEADERS) -DDEBUG_BUILD

all: $(EXEC) cleanobj
MAIN= VideoReader

$(MAIN): $(OBJECTS)
	$(CC) $(CFLAGS) $(INCLUDES) -o $(MAIN) $(OBJECTS) $(LIBS) $(LFLAGS)

%.o: %.cpp
	$(CC) $(CFLAGS) $(LIBS) -c $<  -o $@

cleanobj:
	$(RM) *.o *~

clean:
	$(RM) *.o *~ $(MAIN)
