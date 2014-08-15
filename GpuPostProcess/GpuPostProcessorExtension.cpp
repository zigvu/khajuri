#include "GpuPostProcessor.h"
#include <boost/python.hpp>

BOOST_PYTHON_MODULE(GpuPostProcessor)
{
    boost::python::class_<GpuPostProcessor, boost::noncopyable >( "GpuPostProcessor", boost::python::init<PyObject *>() )
      .add_property("result", &GpuPostProcessor::getDstPython)
      .def("resize", &GpuPostProcessor::resize)
    ;
}
