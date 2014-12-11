#include "VideoDb.h"

VideoDb::VideoDb( std::string db_path ) {
  dbType = LEVELDB; 
  // dbType = LMDB;

  videoFrameReader = NULL;
  label = 0;
  batchSize = 1000;

  if (dbType == LEVELDB){
    leveldb::Options leveldb_options;
    leveldb_options.error_if_exists = true;
    leveldb_options.create_if_missing = true;
    leveldb_options.write_buffer_size = 268435456;

    leveldb::Status leveldb_status = leveldb::DB::Open( leveldb_options, db_path, &leveldb_db );
    CHECK(leveldb_status.ok()) << "Failed to open leveldb " << db_path;
    leveldb_batch = new leveldb::WriteBatch();
  } else if (dbType == LMDB) {
    CHECK_EQ(mkdir(db_path.c_str(), 0744), 0) << "mkdir " << db_path << "failed";
    CHECK_EQ(mdb_env_create(&mdb_env), MDB_SUCCESS) << "mdb_env_create failed";
    CHECK_EQ(mdb_env_set_mapsize(mdb_env, 1099511627776), MDB_SUCCESS) // 1TB
      << "mdb_env_set_mapsize failed";
    CHECK_EQ(mdb_env_open(mdb_env, db_path.c_str(), 0, 0664), MDB_SUCCESS)
      << "mdb_env_open failed";
    CHECK_EQ(mdb_txn_begin(mdb_env, NULL, 0, &mdb_txn), MDB_SUCCESS)
      << "mdb_txn_begin failed";
    CHECK_EQ(mdb_open(mdb_txn, NULL, 0, &mdb_dbi), MDB_SUCCESS)
      << "mdb_open failed. Does the lmdb already exist? ";
  } else {
    CHECK(false) << "Unrecognized db type " << dbType;
  }
}

void VideoDb::setVideoFrameReader( VideoFrameReader *vfr ) {
  videoFrameReader = vfr;
}

VideoDb::~VideoDb(){
  if( videoFrameReader ) {
    videoFrameReader = NULL;
  }

  if (dbType == LEVELDB){
    delete leveldb_batch;
    delete leveldb_db;
  } else if (dbType == LMDB) {
    mdb_close(mdb_env, mdb_dbi);
    mdb_env_close(mdb_env);
  }
}


int VideoDb::savePatch( int frameNum, double scale, int x, int y, int width, int height ) {
  if( videoFrameReader ) {
    VideoReader::Datum datum;

    // LOG(ERROR) << "Processed " << label << " files.";
    int retVal = -1;
    while ( retVal == -1 ) {
      retVal = videoFrameReader->savePatchFromFrameNumberToDatum(
        frameNum, scale, x, y, width, height, label, &datum );
    }
    if( datum.channels() == 0 || datum.height() == 0 || datum.width() == 0 ) {
      // LOG(ERROR) << "Datum details: channels : " << datum.channels()
      //            << " Datum height " << datum.height() 
      //            << " Datum width " << datum.width() ;
      CHECK( false ) << " Issue with " << label;
    }

    std::string value;
    datum.SerializeToString(&value);
    std::string keystr = boost::to_string(label);

    if (dbType == LEVELDB){
      leveldb_batch->Put(keystr, value);
    } else if (dbType == LMDB) {
      mdb_data.mv_size = value.size();
      mdb_data.mv_data = reinterpret_cast<void*>(&value[0]);
      mdb_key.mv_size = keystr.size();
      mdb_key.mv_data = reinterpret_cast<void*>(&keystr[0]);
      CHECK_EQ(mdb_put(mdb_txn, mdb_dbi, &mdb_key, &mdb_data, 0), MDB_SUCCESS) << "mdb_put failed";
    }

    label++;
    if( label % batchSize == 0 ) {
      // LOG(ERROR) << "Reached batch Size " << batchSize << " saving.";
      saveDb();
      // reset batches
      if (dbType == LEVELDB){
        delete leveldb_batch;
        leveldb_batch = new leveldb::WriteBatch();
      } else if (dbType == LMDB) {
        CHECK_EQ(mdb_txn_begin(mdb_env, NULL, 0, &mdb_txn), MDB_SUCCESS) << "mdb_txn_begin failed";
      }
    }

    return label - 1;
  }
  return label;
}

void VideoDb::saveDb() {
  if (dbType == LEVELDB){
    leveldb_db->Write(leveldb::WriteOptions(), leveldb_batch);
  } else if (dbType == LMDB) {
    CHECK_EQ(mdb_txn_commit(mdb_txn), MDB_SUCCESS) << "mdb_txn_commit failed";    
  }
}
