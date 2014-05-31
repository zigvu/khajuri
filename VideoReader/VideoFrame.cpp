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

void VideoFrame::saveFrame(char *fileName, SwsContext *sws_ctx){
  FILE *pFile;
  
  // populate pFrameRGB
  getPFrame(sws_ctx);
  
  // Open file
  pFile=fopen(fileName, "wb");
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

void VideoFrame::saveCroppedFrame( char *fileName, int top, int bottom, int left, int right ){
  cv::Mat image = cv::Mat( getIplImage(), true );
  cv::Rect myROI( top, bottom, left, right );
  cv::Mat croppedImage = image(myROI);
  imwrite( "cropped.jpg", croppedImage );
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


static IplImage* fill_iplimage_from_frame(const AVFrame *frame, enum AVPixelFormat pixfmt)
{
    IplImage *tmpimg;
    int depth, channels_nb;

    if      (pixfmt == AV_PIX_FMT_GRAY8) { depth = IPL_DEPTH_8U;  channels_nb = 1; }
    else if (pixfmt == AV_PIX_FMT_BGRA)  { depth = IPL_DEPTH_8U;  channels_nb = 4; }
    else if (pixfmt == AV_PIX_FMT_BGR24) { depth = IPL_DEPTH_8U;  channels_nb = 3; }
    else return NULL;

    tmpimg = cvCreateImageHeader((CvSize){frame->width, frame->height}, depth, channels_nb);
    tmpimg->imageData = tmpimg->imageDataOrigin = (char *)frame->data[0];
    tmpimg->dataOrder = IPL_DATA_ORDER_PIXEL;
    tmpimg->origin    = IPL_ORIGIN_TL;
    tmpimg->widthStep = frame->linesize[0];
    return tmpimg;
}

IplImage* VideoFrame::getIplImage(){
  if(!iplImage) { 
     iplImage = fill_iplimage_from_frame( pFrame, AV_PIX_FMT_BGR24 );
  }
  return iplImage;
}

caffe::Datum *VideoFrame::getCaffeProtoBuf( int top, int bottom, int left, int right ) {
  GOOGLE_PROTOBUF_VERIFY_VERSION;
  caffe::Datum *protoBuf = new caffe::Datum;
  cv::Mat image = cv::Mat( getIplImage(), true );
  cv::Rect myROI( top, bottom, left, right );
  cv::Mat croppedImage = image(myROI);

  // TODO put the data in protoBuf
  protoBuf->set_data( croppedImage.data, (int)(croppedImage.total()) );
  return protoBuf;
}

