#include "VideoFrameReader.h"
#include <boost/python.hpp>

BOOST_PYTHON_MODULE(VideoReader)
{
    boost::python::class_<VideoFrame>( "VideoFrame", boost::python::init<int, int>() )
			.add_property("timeStamp", &VideoFrame::getTimeStamp, &VideoFrame::setTimeStamp)
			.add_property("frameNum", &VideoFrame::getFrameNumber, &VideoFrame::setFrameNumber)
			//.add_property("avFrame", &VideoFrame::getAVFrame)
			//.add_property("pFrame", &VideoFrame::getPFrame)

    ;
    boost::python::class_<VideoFrameReader, boost::noncopyable >( "VideoFrameReader", boost::python::init<uint, uint, char *>() )
			.add_property("fps", &VideoFrameReader::getFps )
			.add_property("lengthInMicroSeconds", &VideoFrameReader::getLengthInMicroSeconds)
			.add_property("eof", &VideoFrameReader::eof)
                        .def("generateFrames", &VideoFrameReader::startThreads)
                        .def("waitForEOF", &VideoFrameReader::joinThreads)
                        .def("seekToFrameWithFrameNumber", &VideoFrameReader::seekToFrameWithFrameNumber)
                        .def("getFrameWithFrameNumber", &VideoFrameReader::getFrameWithFrameNumber, boost::python::return_internal_reference<>())
                        .def("saveFrameWithFrameNumber", &VideoFrameReader::saveFrameWithFrameNumber)
                        .def("savePngWithFrameNumber", &VideoFrameReader::savePngWithFrameNumber)
                        .def("annotateFrameNumber", &VideoFrameReader::annotateFrameNumber)

    ;

}
