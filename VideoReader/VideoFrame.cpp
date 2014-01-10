#include "VideoFrame.h"

VideoFrame::VideoFrame(int w, int h){
  //DEBUG("VideoFrame: Constructor: Width:%d ; Height: %d\n", w, h);

  width = w;
  height = h;

  pFrame = avcodec_alloc_frame();
  videoFrameNumber = -1;
  videoFrameTimeStamp = -1.0;
}


AVFrame * VideoFrame::getAVFrame(){
  return pFrame;
}

void VideoFrame::setTimeStamp(double timestamp){
  if (videoFrameTimeStamp == -1.0){
    videoFrameTimeStamp = timestamp;
  }
}
double VideoFrame::getTimeStamp(){ return videoFrameTimeStamp; }

void VideoFrame::setFrameNumber(int64_t frameNumber){
  if(videoFrameNumber == -1){
    videoFrameNumber = frameNumber;
  }
}
int64_t VideoFrame::getFrameNumber(){ return videoFrameNumber; }

void VideoFrame::saveFrame(char *fileNamePrefix, SwsContext *sws_ctx){
  FILE *pFile;
  char szFilename[1024];
  
  // populate pFrameRGB
  getPFrame(sws_ctx);
  
  // Open file
  sprintf(szFilename, "%s_%lld.ppm",fileNamePrefix, (long long)getFrameNumber());
  pFile=fopen(szFilename, "wb");
  if(pFile == NULL)
    return;
  
  // Write header
  fprintf(pFile, "P6\n%d %d\n255\n", width, height);
  
  // Write pixel data
  for(int y=0; y<height; y++)
    fwrite(pFrameRGB->data[0]+y*pFrameRGB->linesize[0], 1, width*3, pFile);
  
  // Close file
  fclose(pFile);
}

AVFrame * VideoFrame::getPFrame(SwsContext *sws_ctx){
  if(!pFrameRGB){
    // Allocate an AVFrame structure
    pFrameRGB = avcodec_alloc_frame();
    if(pFrameRGB == NULL){
      throw new std::runtime_error("Couldn't allocate memory to pFrameRGB");
    }

    // Determine required buffer size and allocate buffer
    int numBytes = avpicture_get_size(PIX_FMT_RGB24, width, height);
    buffer = (uint8_t *)av_malloc(numBytes*sizeof(uint8_t));

    avpicture_fill((AVPicture *)pFrameRGB, buffer, PIX_FMT_RGB24, width, height);

    // Convert the image from its native format to RGB
    sws_scale
    (
        sws_ctx,
        (uint8_t const * const *)pFrame->data,
        pFrame->linesize,
        0,
        height,
        pFrameRGB->data,
        pFrameRGB->linesize
    );
  }
  return pFrameRGB;
}

VideoFrame::~VideoFrame(){
	//DEBUG("VideoFrame: Destructor: Frame: %lld; Time: %f\n", (long long)videoFrameNumber, videoFrameTimeStamp);
  
  if(pFrame){ av_free(pFrame); }
  if(pFrameRGB){ av_free(pFrameRGB); }
  if(buffer){ av_free(buffer); }
}