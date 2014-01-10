#include "VideoFrame.h"

#include <boost/thread.hpp>
#include <boost/date_time.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/condition_variable.hpp>

// Define a list that will store VideoFrames
typedef list<VideoFrame> VideoFrameList;

// The disposer object function to delete 
// video frames from list
struct DeleteFrameDisposer
{
  void operator()(VideoFrame *delete_this)
  {  delete delete_this;  }
};

// Class definition
class VideoFrameReader {
  public:
    VideoFrameReader(
      uint listTailBufNumOfFrames_,
      uint listHeadBufNumOfFrames_,
      char *videoFileToOpen);
    ~VideoFrameReader();
    void startThreads();
    void joinThreads();
    void videoFrameBufferProducer();
    void videoFrameBufferConsumer(int numberOfFramesToConsume);
    int saveFrameWithFrameNumber(int64_t frameNumber, char *fileName);
    VideoFrame* getFrameWithFrameNumber(int64_t frameNumber);
    int seekToFrameWithFrameNumber(int64_t frameNumber);
    uint getLengthInMicroSeconds();
    double getFps();

  private:
    // To manage list
    VideoFrameList    videoFrameList;
    int64_t           maxVideoFrameNumber;
    uint              maxVideoFrameListSize;
    uint              listTailBufNumOfFrames;
    uint              listHeadBufNumOfFrames;

    // To manage threads
    boost::thread     producerThread;
    boost::thread     consumerThread;
    boost::mutex      mut;
    bool              data_ready;
    boost::condition_variable cond;

    // To manage frame extraction
    AVFormatContext   *pFormatCtx = NULL;
    int               videoStream;
    AVCodecContext    *pCodecCtx = NULL;
    AVCodec           *pCodec = NULL;
    AVPacket          packet;
    int               frameFinished;
    int               numBytes;
    AVDictionary      *optionsDict = NULL;
    struct SwsContext *sws_ctx = NULL;
    float             time_base;
    AVRational        fps;

    // Frame seek operation:
    // SEEK_SUCCESS --> if getFrameAtSeekPosition is called next, a frame will be returned
    // SEEK_WAIT --> the producer buffer is not ready yet, so wait
    // SEEK_OUT_OF_BOUNDS --> the seek position doesn't exist
    // SEEK_FAIL --> no further retry will guarantee SEEK_SUCCESS
    static const int SEEK_SUCCESS = 1;
    static const int SEEK_WAIT = 0;
    static const int SEEK_OUT_OF_BOUNDS = 2;
    static const int SEEK_FAIL = -1;
};