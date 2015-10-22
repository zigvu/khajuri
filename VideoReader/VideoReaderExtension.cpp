#include "VideoFrameAnnotator.h"
#include <boost/python.hpp>

BOOST_PYTHON_MODULE(VideoReader)
{
    boost::python::class_<VideoFrame>( "VideoFrame", boost::python::init<int, int>() )
			.add_property("timeStamp", &VideoFrame::getTimeStamp, &VideoFrame::setTimeStamp)
			.add_property("frameNum", &VideoFrame::getFrameNumber, &VideoFrame::setFrameNumber)
			.add_property("width", &VideoFrame::getWidth )
			.add_property("height", &VideoFrame::getHeight )
    ;
    boost::python::class_<VideoFrameReader, boost::noncopyable >( "VideoFrameReader", boost::python::init<uint, uint, char *>() )
			.add_property("fps", &VideoFrameReader::getFps )
			.add_property("totalFrames", &VideoFrameReader::getTotalFrames)
			.add_property("eof", &VideoFrameReader::eof)
      .def("generateFrames", &VideoFrameReader::startThreads)
      .def("waitForEOF", &VideoFrameReader::joinThreads)
      .def("seekToFrameWithFrameNumber", &VideoFrameReader::seekToFrameWithFrameNumber)
      .def("getFrameWithFrameNumber", &VideoFrameReader::getFrameWithFrameNumber, boost::python::return_internal_reference<>())
      .def("saveFrameWithFrameNumber", &VideoFrameReader::saveFrameWithFrameNumber)
      .def("savePngWithFrameNumber", &VideoFrameReader::savePngWithFrameNumber)
      .def("savePatchFromFrameNumber", &VideoFrameReader::savePatchFromFrameNumber)
      .def("startLogger", &VideoFrameReader::startLogger)
      .def("stopLogger", &VideoFrameReader::stopLogger)
    ;
    boost::python::class_<VideoFrameAnnotator>( "VideoFrameAnnotator", boost::python::init<char *>() )
			.add_property("currentFrameNum", &VideoFrameAnnotator::currentFrameNum)
      .def("setVideoFrameReader", &VideoFrameAnnotator::setVideoFrameReader)
      .def("addToVideo", &VideoFrameAnnotator::addToVideo)
      .def("addBoundingBox", &VideoFrameAnnotator::addBoundingBox)
    ;
    boost::python::scope in_VideoDb = boost::python::class_<VideoDb, boost::noncopyable >( 
        "VideoDb", boost::python::init<VideoDb::DBTYPE, int>() )
      .def("createNewDb", &VideoDb::createNewDb)
      .def("loadExistingDbReadOnly", &VideoDb::loadExistingDbReadOnly)
      .def("savePatch", &VideoDb::savePatch)
      .def("deletePatch", &VideoDb::deletePatch)
      .def("countPatches", &VideoDb::countPatches)
      .def("saveDb", &VideoDb::saveDb)
    ;
    boost::python::enum_<VideoDb::DBTYPE>("DBTYPE")
      .value("LEVELDB", VideoDb::LEVELDB)
      .value("LMDB", VideoDb::LMDB)
      .export_values()
    ;
}
