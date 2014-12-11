#include "VideoFrameReader.h"
#include <glog/logging.h>
#include <leveldb/db.h>
#include <leveldb/write_batch.h>
#include <lmdb.h>
#include "caffe.pb.h"

#include <string>
#include <sys/stat.h>

class VideoDb {
  public:
    enum DBTYPE { LEVELDB = 1, LMDB = 2 };

    VideoDb( DBTYPE db_type, int batch_size );
    ~VideoDb();

    void createNewDb( std::string db_path );

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

    // lmdb related
    MDB_env *mdb_env;
    MDB_dbi mdb_dbi;
    MDB_val mdb_key, mdb_data;
    MDB_txn *mdb_txn;
};
