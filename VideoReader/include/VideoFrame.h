#ifdef __cplusplus
  #define __STDC_CONSTANT_MACROS
  #ifdef _STDINT_H
    #undef _STDINT_H
  #endif
  extern "C" {
    #include <stdint.h>
    #include <libavcodec/avcodec.h>
    #include <libavformat/avformat.h>
    #include <libswscale/swscale.h>
  }
#endif

#include <stdexcept>
#include <boost/intrusive/list.hpp>
#include <opencv2/opencv.hpp>

#include <glog/logging.h>
#include "caffe.pb.h"
using namespace boost::intrusive;

#ifdef DEBUG_BUILD
#define DEBUG(format, args...) do { fprintf(stderr, format, args); } while (0)
#else
#define DEBUG(format, args...) do {} while (0)
#endif

class VideoFrame : public list_base_hook<>{
	public:
		VideoFrame(int w, int h);
		~VideoFrame();
		AVFrame * getAVFrame();
		void setTimeStamp(double timestamp);
		double getTimeStamp();
		int getWidth();
		int getHeight();
		void setFrameNumber(int64_t frameNumber);
		int64_t getFrameNumber();
		void saveFrame(char *fileNamePrefix, SwsContext *sws_ctx);
		void savePng(char *fileNamePrefix, SwsContext *sws_ctx);
    void saveCroppedFrame( char *fileNamePrefix, SwsContext *sws_ctx, float scale, int x, int y, int width, int height );
		AVFrame * getPFrame(SwsContext *sws_ctx);
    void saveCroppedFrameToDatum( float scale, int x, int y, int width, int height, int label, VideoReader::Datum *datum );

	private:
    IplImage *iplImage;
		AVFrame *pFrame;
		AVFrame *dst;
	  uint8_t *buffer;

	  int width;
	  int height;

	  int64_t videoFrameNumber;
	  double videoFrameTimeStamp;
    std::map< float, cv::Mat *> scaledFrames;
};
