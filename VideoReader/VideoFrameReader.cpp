#include "VideoFrameReader.h"

// Constructor - set up video reading
VideoFrameReader::VideoFrameReader(
    uint listTailBufNumOfFrames_,
    uint listHeadBufNumOfFrames_,
    char *videoFileToOpen) {
  
  DEBUG("%s\n", "VideoFrameReader: Constructor");

  // initialize values to NULL
  pFormatCtx = NULL;
  pFormatCtx = NULL;
  pCodecCtx = NULL;
  pCodec = NULL;
  optionsDict = NULL;
  sws_ctx = NULL;

  // Register all formats and codecs
  av_register_all();

  // Open video file
  if(avformat_open_input(&pFormatCtx, videoFileToOpen, NULL, NULL)!=0){
    throw new std::runtime_error("Couldn't open file");
  }

  // Retrieve stream information
  if(avformat_find_stream_info(pFormatCtx, NULL)<0){
    throw new std::runtime_error("Couldn't find stream information");
  }

  // Dump information about file onto standard error
  av_dump_format(pFormatCtx, 0, videoFileToOpen, 0);

  // Find the first video stream
  videoStream=-1;
  for(uint i=0; i<pFormatCtx->nb_streams; i++){
    if(pFormatCtx->streams[i]->codec->codec_type==AVMEDIA_TYPE_VIDEO) {
      videoStream=i;
      fps = pFormatCtx->streams[i]->r_frame_rate;
      time_base = pFormatCtx->streams[i]->time_base.num / 
          ( 1.0 * pFormatCtx->streams[i]->time_base.den );
      break;
    }
  }
  if(videoStream==-1){
    throw new std::runtime_error("Didn't find a video stream");
  }
  
  // Get a pointer to the codec context for the video stream
  pCodecCtx=pFormatCtx->streams[videoStream]->codec;
  
  // Find the decoder for the video stream
  pCodec=avcodec_find_decoder(pCodecCtx->codec_id);
  if(pCodec==NULL) {
    throw new std::runtime_error("Unsupported codec");
  }

  // Open codec
  if(avcodec_open2(pCodecCtx, pCodec, &optionsDict)<0) {
    throw new std::runtime_error("Not able to open codec information");
  }

  sws_ctx =
    sws_getContext(
      pCodecCtx->width,
      pCodecCtx->height,
      pCodecCtx->pix_fmt,
      pCodecCtx->width,
      pCodecCtx->height,
      PIX_FMT_RGB24,
      SWS_BILINEAR,
      NULL,
      NULL,
      NULL
    );

  listTailBufNumOfFrames = listTailBufNumOfFrames_;
  listHeadBufNumOfFrames = listHeadBufNumOfFrames_;
  maxVideoFrameListSize = listTailBufNumOfFrames + listHeadBufNumOfFrames;
  data_ready = true;
  maxVideoFrameNumber = LLONG_MAX; // set to max possible for now
  eof = false;

}

void VideoFrameReader::stopLogger(){
  google::ShutdownGoogleLogging();
}

void VideoFrameReader::startThreads(){
  DEBUG("%s\n", "Thread: Producer: Starting thread");
  producerThread = boost::thread(&VideoFrameReader::videoFrameBufferProducer, this);
  // Note: consumer currently runs in main thread
  //consumerThread = boost::thread(&VideoFrameReader::videoFrameBufferConsumer, this);
}
void VideoFrameReader::joinThreads(){
  DEBUG("%s\n", "Thread: Producer: Joining thread");
  producerThread.join();
  // Note: consumer currently runs in main thread
  //consumerThread.join();
}

void VideoFrameReader::startLogger(){
  ::google::InitGoogleLogging( "VideoFrameReader" );    
}

void VideoFrameReader::videoFrameBufferProducer(){
  VideoFrame *vf;
  bool wasLastFrameFinished = true;
  int64_t frameNumber = 0;

  DEBUG("%s\n", "Thread: Producer: Start producing");
  // until we can read new frames
  while (av_read_frame(pFormatCtx, &packet)>=0){
    // set mutex and wait
    boost::unique_lock<boost::mutex> lock(mut);
    while(!data_ready) {
      DEBUG("Thread: Producer: Lock waiting at frame: %lld\n", (long long)frameNumber);
      cond.wait(lock);
      DEBUG("Thread: Producer: Lock released at frame: %lld\n", (long long)frameNumber);
    }

    // Is this a packet from the video stream?
    if(packet.stream_index==videoStream) {
      if (wasLastFrameFinished){
        vf = new VideoFrame(pCodecCtx->width, pCodecCtx->height);
      }

      // Decode video frame
      avcodec_decode_video2(pCodecCtx, vf->getAVFrame(), &frameFinished, &packet);
      // Did we get a video frame?
      if(frameFinished) {
        DEBUG("Thread: Producer: Pushing to list: frame: %lld\n", (long long)frameNumber);
        wasLastFrameFinished = true;

        vf->setFrameNumber(frameNumber++);
        maxVideoFrameNumber = frameNumber - 1;
        vf->setTimeStamp(packet.pts * time_base); // this will be ignored if not new frame

	      vf->readPFrame( sws_ctx );
        videoFrameList.push_front(*vf);
        if(videoFrameList.size() >= maxVideoFrameListSize){
          data_ready = false;
        }
      } else {
        // continue saving to same VideoFrame object
        wasLastFrameFinished = false;
        vf->setTimeStamp(packet.pts * time_base);
      }
    }

    // Free the packet that was allocated by av_read_frame
    av_free_packet(&packet);
  }
  // when done reading, we know max frame size
  maxVideoFrameNumber = frameNumber - 1;
  eof = true;
}

void VideoFrameReader::videoFrameBufferConsumer(int numberOfFramesToConsume){
  DEBUG("%s\n", "Thread: Consumer: Start consuming");

  while((videoFrameList.size() > 0) && (numberOfFramesToConsume-- > 0)){
    DEBUG("Thread: Consumer: Delete and dispose frame: %lld; List length: %lu\n", 
      (long long)videoFrameList.back().getFrameNumber(), videoFrameList.size());

    videoFrameList.pop_back_and_dispose(DeleteFrameDisposer());
  }

  // inform that some parts of queue have been emptied
  {
    boost::lock_guard<boost::mutex> lock(mut);
    data_ready=true;
  }
  cond.notify_one();

  DEBUG("%s\n", "Thread: Consumer: Finished consuming");
}

int VideoFrameReader::saveFrameWithFrameNumber(int64_t frameNumber, char *fileName){
  DEBUG("VideoFrameReader: saveFrameWithFrameNumber: %lld\n", (long long)frameNumber);
  VideoFrame *retVideoFrame = getFrameWithFrameNumber(frameNumber);
  if(retVideoFrame != NULL){
    retVideoFrame->saveFrame(fileName);
    return 0;
  }
  return -1;
}

int VideoFrameReader::savePngWithFrameNumber(int64_t frameNumber, char *fileName){
  DEBUG("VideoFrameReader: savePngWithFrameNumber: %lld\n", (long long)frameNumber);
  VideoFrame *retVideoFrame = getFrameWithFrameNumber(frameNumber);
  if(retVideoFrame != NULL){
    retVideoFrame->savePng(fileName);
    return 0;
  }
  return -1;
}

int VideoFrameReader::savePatchFromFrameNumber(int64_t frameNumber, char *fileName, double scale,
    int x, int y, int width, int height){
  DEBUG("VideoFrameReader: savePatchFromFrameNumber: %lld\n", (long long)frameNumber);
  VideoFrame *retVideoFrame = getFrameWithFrameNumber(frameNumber);
  if(retVideoFrame != NULL){
    retVideoFrame->saveCroppedFrame(fileName, scale, x, y, width, height);
    return 0;
  }
  return -1;
}

int VideoFrameReader::savePatchFromFrameNumberToDatum(int64_t frameNumber, double scale,
    int x, int y, int width, int height, int label, VideoReader::Datum *datum ) {
  DEBUG("VideoFrameReader: savePatchFromFrameNumberToDatum: %lld\n", (long long)frameNumber);
  VideoFrame *retVideoFrame = getFrameWithFrameNumber(frameNumber);
  if(retVideoFrame != NULL){
    retVideoFrame->saveCroppedFrameToDatum(scale, x, y, width, height, label, datum );
    return 0;
  }
  return -1;
}


VideoFrame* VideoFrameReader::getFrameWithFrameNumber(int64_t frameNumber){
  DEBUG("VideoFrameReader: getFrameWithFrameNumber: %lld\n", (long long)frameNumber);
  int retVal = seekToFrameWithFrameNumber(frameNumber);
  if (retVal == SEEK_SUCCESS){
    VideoFrameList::reverse_iterator vflBegin(videoFrameList.rbegin()), vflEnd(videoFrameList.rend());
    for(; vflBegin != vflEnd; ++vflBegin){
      if ((*vflBegin).getFrameNumber() == frameNumber){
        DEBUG("VideoFrameReader: getFrameWithFrameNumber: Found frame: %lld\n", (long long)frameNumber);
        return &(*vflBegin);
      }
    }
  } else if ((retVal == SEEK_FAIL) || (retVal == SEEK_OUT_OF_BOUNDS) || (retVal == SEEK_WAIT)){
    DEBUG("VideoFrameReader: getFrameWithFrameNumber: Did not find frame: %lld\n", (long long)frameNumber);
    // do nothing for now
  }
  return NULL;
}
/*
  List description:

      |<----tail---->|<----head---->|

  Addition to head, deletion from tail
*/

int VideoFrameReader::seekToFrameWithFrameNumber(int64_t frameNumber){
  
  if((frameNumber < 0) || (frameNumber > maxVideoFrameNumber && eof)){
    DEBUG("VideoFrameReader: seekToFrameWithFrameNumber: SEEK_OUT_OF_BOUNDS: Request: %lld, Max: %lld\n", 
      (long long)frameNumber, (long long)maxVideoFrameNumber);

    return SEEK_OUT_OF_BOUNDS;
  }
  // if we have already read and moved beyond the frame
  if(frameNumber < videoFrameList.back().getFrameNumber()){
    DEBUG("%s\n","VideoFrameReader: seekToFrameWithFrameNumber: SEEK_FAIL - beyond tail");

    return SEEK_FAIL;
  }
  // if it is in the tail region, no need to change list
  if((frameNumber >= videoFrameList.back().getFrameNumber())
    && ((frameNumber - videoFrameList.back().getFrameNumber()) < listTailBufNumOfFrames)
    && frameNumber <= videoFrameList.front().getFrameNumber() ){
    DEBUG("%s\n","VideoFrameReader: seekToFrameWithFrameNumber: SEEK_SUCCESS - within tail");

    return SEEK_SUCCESS;
  }
  // if it is in the head region, change tail so that this request frame
  // becomes the middle frame of the tail region
  if(frameNumber <= videoFrameList.front().getFrameNumber()){
    DEBUG("%s\n","VideoFrameReader: seekToFrameWithFrameNumber: SEEK_SUCCESS - within head");

    int64_t newTailStartFrameNumber = frameNumber - listTailBufNumOfFrames/2;
    int64_t numberOfFramesToConsume = 
      newTailStartFrameNumber - 
      videoFrameList.back().getFrameNumber();
    
    // move sliding window by consuming frames:
    videoFrameBufferConsumer(numberOfFramesToConsume);
    return SEEK_SUCCESS;
  }

  // if it is beyond the head region, consume and recurse
  if(frameNumber > videoFrameList.front().getFrameNumber()){
    DEBUG("%s\n","VideoFrameReader: seekToFrameWithFrameNumber: SEEK_WAIT - outside head");

    // put the last frame in the middle of the tail region
    int64_t newTailStartFrameNumber = 
      videoFrameList.front().getFrameNumber() - 
      listTailBufNumOfFrames/2;
    int64_t numberOfFramesToConsume = 
      newTailStartFrameNumber - 
      videoFrameList.back().getFrameNumber();

    // move sliding window by consuming frames:
    videoFrameBufferConsumer(numberOfFramesToConsume);

    // TODO: remove wait with mutex:
    boost::posix_time::seconds workTime(0.01);
    boost::this_thread::sleep(workTime);

    return seekToFrameWithFrameNumber(frameNumber);
  }
  
  return SEEK_FAIL;
}

double VideoFrameReader::getFps(){
  return (double)fps.num/fps.den ;
}

int VideoFrameReader::getTotalFrames(){
  return maxVideoFrameNumber;
}


VideoFrameReader::~VideoFrameReader() {
  while( !eof ) {
    seekToFrameWithFrameNumber( maxVideoFrameNumber );
  }
  joinThreads();
  // clear out any remaining frames from list
  videoFrameList.clear_and_dispose(DeleteFrameDisposer());

  // Close the codec
  if(pCodecCtx){ avcodec_close(pCodecCtx); }
  
  // Close the video file
  if(pFormatCtx){ avformat_close_input(&pFormatCtx); }

  // Close the context
  if(sws_ctx){ sws_freeContext(sws_ctx); }
}
