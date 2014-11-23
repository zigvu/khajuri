#include "VideoFrameAnnotator.h"

VideoFrameAnnotator::VideoFrameAnnotator( std::string fileName ) {
  vfr = NULL;
  currentFrameNum = 0;
  videoFileName = fileName;
  outputVideo = NULL;
}


void VideoFrameAnnotator::setVideoFrameReader( VideoFrameReader *videoFrameReader ) {
  vfr = videoFrameReader;
}

VideoFrameAnnotator::~VideoFrameAnnotator(){
  if( vfr ) {
    vfr = NULL;
  }
}

void VideoFrameAnnotator::addToVideo( int frameNum, bool eval ) {
  if( vfr ) {
    VideoFrame *vFrame = vfr->getFrameWithFrameNumber( frameNum );
    if( vFrame ) {
       cv::Mat * m = vFrame->getMat();
       int w = vFrame->getWidth(), h = vFrame->getHeight();
       char frameNumber[100];
       sprintf( frameNumber, "FN#%d", frameNum );
       std::string frameNumString = frameNumber ;
       cv::putText( *m, frameNumString, cv::Point(30,30), 
           cv::FONT_HERSHEY_COMPLEX_SMALL, 0.8, cv::Scalar(256,256,256), 1, CV_AA);
       if( eval ) {
        cv::putText( *m, "*", cv::Point(15,30),
            cv::FONT_HERSHEY_COMPLEX_SMALL, 0.8, cv::Scalar(256,256,256), 1, CV_AA);
       }

       if( !outputVideo ) {
         outputVideo = new cv::VideoWriter;
         outputVideo->open( videoFileName, CV_FOURCC('P','I','M','1'),
             25, cv::Size( w, h ) , true);
       }
       *outputVideo << *m;
    }
  }
}

int VideoFrameAnnotator::addBoundingBox( int frameNum, int x, int y, int width, int height, int classId, float score ) {
  VideoFrame * vFrame;
  if( frameNum < currentFrameNum ) {
    return -1;
  }
  if( vfr ) {
    vFrame = vfr->getFrameWithFrameNumber( frameNum );
    while( vFrame == NULL) {
      vFrame = vfr->getFrameWithFrameNumber( frameNum );
      if( vfr->eof ) {
        return -1;
      }
    }
    cv::Mat * m = vFrame->getMat();
    char txt[50];
    sprintf( txt, "%d:%.2f", classId, score );
    cv::putText( *m, txt, cv::Point( x + 30, y + 30 ), 
        cv::FONT_HERSHEY_COMPLEX_SMALL, 0.8, cv::Scalar(256,256,256), 1, CV_AA);
    cv::rectangle( *m, cv::Point( x, y ),
        cv::Point( x + width, y + height ),
        cv::Scalar(0,0,256),
        2 );
  }
  currentFrameNum = frameNum;
  return 0;
}
