#include "VideoFrame.h"

#include <boost/thread.hpp>
#include <boost/date_time.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/condition_variable.hpp>
#include <glog/logging.h>
#include <leveldb/db.h>
#include <leveldb/write_batch.h>

class VideoDb;
// Define a list that will store VideoFrames
typedef boost::intrusive::list<VideoFrame> VideoFrameList;

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
      char * videoFileToOpen);
    ~VideoFrameReader();
    void startThreads();
    void startLogger();
    void stopLogger();
    void joinThreads();
    void videoFrameBufferProducer();
    void videoFrameBufferConsumer(int numberOfFramesToConsume);
    int saveFrameWithFrameNumber(int64_t frameNumber, char *fileName);
    int savePngWithFrameNumber(int64_t frameNumber, char *fileName);
    int savePatchFromFrameNumber(int64_t frameNumber, char *fileName, double scale,
        int x, int y, int width, int height );
    int savePatchFromFrameNumberToDatum(int64_t frameNumber, double scale,
        int x, int y, int width, int height, int label, VideoReader::Datum *datum );
    VideoFrame* getFrameWithFrameNumber(int64_t frameNumber);
    int seekToFrameWithFrameNumber(int64_t frameNumber);
    int64_t getLengthInMicroSeconds();
    double getFps();
    int getTotalFrames();
    
    bool eof;

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
    AVFormatContext   *pFormatCtx;
    int               videoStream;
    AVCodecContext    *pCodecCtx;
    AVCodec           *pCodec;
    AVPacket          packet;
    int               frameFinished;
    int               numBytes;
    AVDictionary      *optionsDict;
    struct SwsContext *sws_ctx;
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
