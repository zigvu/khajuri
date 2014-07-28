#include "VideoLevelDb.h"

VideoLevelDb::VideoLevelDb( std::string fileName ) {
  leveldb::Options options;
  options.error_if_exists = true;
  options.create_if_missing = true;
  options.write_buffer_size = 268435456;
  leveldb::Status status = leveldb::DB::Open( options, fileName, &db);
  CHECK(status.ok()) << "Failed to open leveldb " << fileName;
  batch = new leveldb::WriteBatch();
  vfr = NULL;
  label = 0;
  batchSize = 1000;
}


void VideoLevelDb::setVideoFrameReader( VideoFrameReader *videoFrameReader ) {
  vfr = videoFrameReader;
}

VideoLevelDb::~VideoLevelDb(){
  if( vfr ) {
    vfr = NULL;
  }
  if( batch ) {
    delete batch;
  }
  if( db ) {
    delete db;
  }
}


int VideoLevelDb::savePatch( int frameNum, float scale, int x, int y, int width, int height ) {
  if( vfr ) {
    VideoReader::Datum datum;
    // LOG(ERROR) << "Processed " << label << " files.";
    int retVal = -1;
    while ( retVal == -1 ) {
      retVal = vfr->savePatchFromFrameNumberToLevelDb(
          frameNum, scale, x, y, width, height, label,&datum );
    }
    if( datum.channels() == 0 ||
        datum.height() == 0 ||
        datum.width() == 0 ) {
      // LOG(ERROR) << "Datum details: channels : " << datum.channels()
      //            << " Datum height " << datum.height() 
      //            << " Datum width " << datum.width() ;
      CHECK( false ) << " Issue with " << label;
    }

    std::string value;
    datum.SerializeToString(&value);
    batch->Put( boost::to_string( label ), value );
    label++;
    if( label % batchSize == 0 ) {
      // LOG(ERROR) << "Reached batch Size " << batchSize << " saving.";
      saveLevelDb();
      delete batch;
      batch = new leveldb::WriteBatch();
    }
  }
  return label;
}

void VideoLevelDb::saveLevelDb() {
  // LOG(ERROR) << "Saving current batch.";
  db->Write(leveldb::WriteOptions(), batch);
}
