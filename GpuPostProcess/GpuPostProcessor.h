#include "opencv2/opencv.hpp"
#include "opencv2/gpu/gpu.hpp"
#include <boost/python.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include "conversion.h"

class GpuPostProcessor {
  private:
  cv::gpu::GpuMat gpuSrc;
  cv::gpu::GpuMat gpuDst;

  public:
  GpuPostProcessor( std::string filename );
  GpuPostProcessor( cv::Mat src);
  GpuPostProcessor( PyObject * o);
  void resize( float scaleX, float scaleY );
  cv::Mat getDst();
  PyObject *getDstPython();
};
