#include "VideoFrameReader.h"
#include <glog/logging.h>
#include <string>
#include <leveldb/db.h>
#include <leveldb/write_batch.h>
#include "caffe.pb.h"

class VideoDb {
  public:
    VideoDb( std::string fileName );
    ~VideoDb();
    enum DBTYPE { LEVELDB, LMDB };

    void setVideoFrameReader( VideoFrameReader *vfr );
    int savePatch( int frameNum, double scale, int x, int y, int width, int height );
    void saveDb();

  private:
    DBTYPE dbType;

    int label;
    VideoFrameReader *videoFrameReader;
    int batchSize;

    // leveldb related
    leveldb::DB* leveldb_db;
    leveldb::WriteBatch* leveldb_batch;
    int saveLevelDbPatch( int frameNum, double scale, int x, int y, int width, int height );
    void saveLevelDb();

};
