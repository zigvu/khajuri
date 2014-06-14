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
#include "caffe.pb.h"
#include <opencv2/opencv.hpp>

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
		void setFrameNumber(int64_t frameNumber);
		int64_t getFrameNumber();
		void saveFrame(char *fileNamePrefix, SwsContext *sws_ctx);
		void saveCroppedFrame(char *fileNamePrefix, int top, int bottom, int left, int right );
		void savePng(char *fileNamePrefix, SwsContext *sws_ctx);
    void saveAnnotatedFrame( char *fileNamePrefix, SwsContext *sws_ctx, int x, int y, int width, int height );
		AVFrame * getPFrame(SwsContext *sws_ctx);
    IplImage* getIplImage();
    caffe::Datum *getCaffeProtoBuf( int top, int bottom, int left, int right );

	private:
    IplImage *iplImage;
		AVFrame *pFrame;
	  AVFrame *pFrameRGB;
	  uint8_t *buffer;

	  int width;
	  int height;

	  int64_t videoFrameNumber;
	  double videoFrameTimeStamp;
};
