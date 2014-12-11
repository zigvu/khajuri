#include "VideoDb.h"
#include <boost/python.hpp>

BOOST_PYTHON_MODULE(VideoReader)
{
    boost::python::class_<VideoFrame>( "VideoFrame", boost::python::init<int, int>() )
			.add_property("timeStamp", &VideoFrame::getTimeStamp, &VideoFrame::setTimeStamp)
			.add_property("frameNum", &VideoFrame::getFrameNumber, &VideoFrame::setFrameNumber)
			.add_property("width", &VideoFrame::getWidth )
			.add_property("height", &VideoFrame::getHeight )
			//.add_property("avFrame", &VideoFrame::getAVFrame)
			//.add_property("pFrame", &VideoFrame::getPFrame)

    ;
    boost::python::class_<VideoFrameReader, boost::noncopyable >( "VideoFrameReader", boost::python::init<uint, uint, char *>() )
			.add_property("fps", &VideoFrameReader::getFps )
			.add_property("lengthInMicroSeconds", &VideoFrameReader::getLengthInMicroSeconds)
			.add_property("totalFrames", &VideoFrameReader::getTotalFrames)
			.add_property("eof", &VideoFrameReader::eof)
      .def("generateFrames", &VideoFrameReader::startThreads)
      .def("waitForEOF", &VideoFrameReader::joinThreads)
      .def("seekToFrameWithFrameNumber", &VideoFrameReader::seekToFrameWithFrameNumber)
      .def("getFrameWithFrameNumber", &VideoFrameReader::getFrameWithFrameNumber, boost::python::return_internal_reference<>())
      .def("saveFrameWithFrameNumber", &VideoFrameReader::saveFrameWithFrameNumber)
      .def("savePngWithFrameNumber", &VideoFrameReader::savePngWithFrameNumber)
      .def("patchFromFrameNumber", &VideoFrameReader::patchFromFrameNumber)
      .def("startLogger", &VideoFrameReader::startLogger)
    ;
    boost::python::class_<VideoDb, boost::noncopyable >( "VideoDb", boost::python::init<char *>() )
      .def("savePatch", &VideoDb::savePatch)
      .def("saveDb", &VideoDb::saveDb)
      .def("setVideoFrameReader", &VideoDb::setVideoFrameReader)
    ;

}
