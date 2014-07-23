#include "VideoFrame.h"

VideoFrame::VideoFrame(int w, int h){
  //DEBUG("VideoFrame: Constructor: Width:%d ; Height: %d\n", w, h);

  width = w;
  height = h;

  pFrame = NULL;
  dst = NULL;
  buffer = NULL;
  iplImage = NULL;

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
int VideoFrame::getWidth(){ return width; }
int VideoFrame::getHeight(){ return height; }

void VideoFrame::setFrameNumber(int64_t frameNumber){
  if(videoFrameNumber == -1){
    videoFrameNumber = frameNumber;
  }
}
int64_t VideoFrame::getFrameNumber(){ return videoFrameNumber; }

void VideoFrame::saveFrame(char *fileName, SwsContext *sws_ctx){
  FILE *pFile;
  
  // populate dst
  getPFrame(sws_ctx);
  
  // Open file
  pFile=fopen(fileName, "wb");
  if(pFile == NULL)
    return;
  
  // Write header
  fprintf(pFile, "P6\n%d %d\n255\n", width, height);
  
  // Write pixel data
  for(int y=0; y<height; y++)
    fwrite(dst->data[0]+y*dst->linesize[0], 1, width*3, pFile);
  
  // Close file
  fclose(pFile);
}

void VideoFrame::savePng( char*fileName, SwsContext *sws_ctx ) {
  cv::Mat m; 
  int w = pFrame->width, h = pFrame->height;
  m = cv::Mat(h, w, CV_8UC3, dst->data[ 0 ]);
  cv::imwrite( fileName, m );
}

void VideoFrame::saveCroppedFrameToDatum( float scale, int x, int y, 
    int width, int height, int label, VideoReader::Datum *datum ) {
  if( scaledFrames.find( scale ) == scaledFrames.end() ) {
    int w = pFrame->width, h = pFrame->height;
    cv::Mat * m = new cv::Mat(h, w, CV_8UC3, dst->data[ 0 ]);
    cv::Size size = cv::Size( w * scale, h * scale );
    cv::resize( *m, *m, size );
    scaledFrames[ scale ] = m;
  }
  cv::Mat *m = scaledFrames[ scale ];
  cv::Rect myROI( x, y, width, height );
  cv::Mat croppedImage = (*m)(myROI);

  datum->set_channels(3);
  datum->set_height(croppedImage.rows);
  datum->set_width(croppedImage.cols);
  datum->set_label(label);
  datum->clear_data();
  datum->clear_float_data();
  std::string* datum_string = datum->mutable_data();
  for (int c = 0; c < 3; ++c) {
    for (int h = 0; h < croppedImage.rows; ++h) {
      for (int w = 0; w < croppedImage.cols; ++w) {
        datum_string->push_back(
            static_cast<char>(croppedImage.at<cv::Vec3b>(h, w)[c]));
      }
    }
  }
}

void VideoFrame::saveCroppedFrame( char *fileName, SwsContext *sws_ctx, float scale, int x, int y, int width, int height ){
  if( scaledFrames.find( scale ) == scaledFrames.end() ) {
    int w = pFrame->width, h = pFrame->height;
    cv::Mat * m = new cv::Mat(h, w, CV_8UC3, dst->data[ 0 ]);
    cv::Size size = cv::Size( w * scale, h * scale );
    cv::resize( *m, *m, size );
    scaledFrames[ scale ] = m;
  }
  cv::Mat *m = scaledFrames[ scale ];
  cv::Rect myROI( x, y, width, height );
  cv::Mat croppedImage = (*m)(myROI);
  imwrite( fileName, croppedImage );
}

AVFrame * VideoFrame::getPFrame(SwsContext *sws_ctx){
  if(!dst){
    dst = avcodec_alloc_frame();
    memset(dst, 0, sizeof(*dst));
    int w = pFrame->width, h = pFrame->height;
    int numBytes = avpicture_get_size(PIX_FMT_BGR24, w, h);
    buffer = (uint8_t *)av_malloc(numBytes*sizeof(uint8_t));
    avpicture_fill( (AVPicture *)dst, buffer, PIX_FMT_BGR24, w, h);
  
    struct SwsContext *convert_ctx=NULL;
    enum PixelFormat src_pixfmt = (enum PixelFormat)pFrame->format;
    enum PixelFormat dst_pixfmt = PIX_FMT_BGR24;
    convert_ctx = sws_getContext(w, h, src_pixfmt, w, h, dst_pixfmt,
        SWS_FAST_BILINEAR, NULL, NULL, NULL);
    sws_scale(convert_ctx, pFrame->data, pFrame->linesize, 0, h,
        dst->data, dst->linesize);
    sws_freeContext(convert_ctx);
  }
  
  return dst;
}

VideoFrame::~VideoFrame(){
	//DEBUG("VideoFrame: Destructor: Frame: %lld; Time: %f\n", (long long)videoFrameNumber, videoFrameTimeStamp);
  
  if(pFrame){ av_free(pFrame); }
  if(dst){ av_free(dst); }
  if(buffer){ av_free(buffer); }
  for (std::map<float,cv::Mat *>::iterator it=scaledFrames.begin(); it!=scaledFrames.end(); ++it) {
    delete it->second;
  }
}
