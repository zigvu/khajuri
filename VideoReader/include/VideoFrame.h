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
		AVFrame * getPFrame(SwsContext *sws_ctx);

	private:
		AVFrame *pFrame = NULL;
	  AVFrame *pFrameRGB = NULL;
	  uint8_t *buffer = NULL;

	  int width;
	  int height;

	  int64_t videoFrameNumber;
	  double videoFrameTimeStamp;
};