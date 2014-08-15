#include <iostream>
#include "GpuPostProcessor.h"

GpuPostProcessor::GpuPostProcessor( cv::Mat src) {
  gpuSrc.upload( src );
}

GpuPostProcessor::GpuPostProcessor( PyObject * o) {
  NDArrayConverter converter = NDArrayConverter();
  cv::Mat src = converter.toMat( o );
  gpuSrc.upload( src );
}

GpuPostProcessor::GpuPostProcessor( std::string filename ) {
  cv::Mat src = cv::imread(filename.c_str(), CV_LOAD_IMAGE_UNCHANGED);
  gpuSrc.upload( src );
}

void GpuPostProcessor::resize( float scaleX, float scaleY ) {
  cv::gpu::resize( gpuSrc,  gpuDst, cv::Size(0, 0), scaleX, scaleY );
}

cv::Mat GpuPostProcessor::getDst() {
  cv::Mat dst;
  gpuDst.download( dst );
  return dst;
}

PyObject * GpuPostProcessor::getDstPython() {
  NDArrayConverter converter = NDArrayConverter();
  cv::Mat dst;
  gpuDst.download( dst );
  return converter.toNDArray( dst );
}

int main (int argc, char* argv[])
{
  GpuPostProcessor processor = GpuPostProcessor( "file.png" );
  processor.resize( 0.3, 0.3 );
  cv::Mat result_host = processor.getDst();
  cv::imwrite( "file.resized.png", result_host );
  return 0;
}
