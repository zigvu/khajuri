#include "VideoDb.h"
#include <glog/logging.h>
#include <string>
#include <opencv2/opencv.hpp>

class VideoFrameAnnotator {
	public:
		VideoFrameAnnotator( std::string fileName );
		~VideoFrameAnnotator();
		void setVideoFrameReader( VideoFrameReader *videoFrameReader );
    int addBoundingBox( int frameNum, int x, int y, int width, int height, int classId, float score );
    void addToVideo( int frameNum, bool eval );
    int currentFrameNum;

	private:
    cv::VideoWriter *outputVideo;
    VideoFrameReader *vfr;
    std::string videoFileName;
};
