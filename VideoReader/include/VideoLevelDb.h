#include "VideoFrameReader.h"
#include <glog/logging.h>
#include <string>
#include <leveldb/db.h>
#include <leveldb/write_batch.h>
#include "caffe.pb.h"

class VideoLevelDb {
	public:
		VideoLevelDb( std::string fileName );
		~VideoLevelDb();
    int savePatch( int frameNum, float scale, int x, int y, int width, int height );
    void saveLevelDb();
		void setVideoFrameReader( VideoFrameReader *videoFrameReader );

	private:
    leveldb::DB* db;
    leveldb::Options options;
    leveldb::WriteBatch* batch;
    int label;
    VideoFrameReader *vfr;
    int batchSize;

 };
