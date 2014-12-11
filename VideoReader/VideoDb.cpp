#include "VideoDb.h"

VideoDb::VideoDb( std::string fileName ) {
  dbType = LEVELDB; // dbType = LMDB;

  videoFrameReader = NULL;
  label = 0;
  batchSize = 1000;

  if (dbType == LEVELDB){
    leveldb::Options leveldb_options;
    leveldb_options.error_if_exists = true;
    leveldb_options.create_if_missing = true;
    leveldb_options.write_buffer_size = 268435456;

    leveldb::Status leveldb_status = leveldb::DB::Open( leveldb_options, fileName, &leveldb_db );
    CHECK(leveldb_status.ok()) << "Failed to open leveldb " << fileName;
    leveldb_batch = new leveldb::WriteBatch();
  } else if (dbType == LMDB) {

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
    if( leveldb_batch ) { delete leveldb_batch; }
    if( leveldb_db ) { delete leveldb_db; }
  } else if (dbType == LMDB) {

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

    }

    label++;
    if( label % batchSize == 0 ) {
      // LOG(ERROR) << "Reached batch Size " << batchSize << " saving.";
      saveDb();
      // reset batches
      if (dbType == LEVELDB){
        //saveLevelDb();
        delete leveldb_batch;
        leveldb_batch = new leveldb::WriteBatch();
      } else if (dbType == LMDB) {

      }
    }

    return label - 1;
  }
  return label;
}

// int VideoDb::saveLevelDbPatch( int frameNum, double scale, int x, int y, int width, int height ) {
//   if( videoFrameReader ) {
//     VideoReader::Datum datum;
//     // LOG(ERROR) << "Processed " << label << " files.";
//     int retVal = -1;
//     while ( retVal == -1 ) {
//       retVal = videoFrameReader->savePatchFromFrameNumberToDatum(
//           frameNum, scale, x, y, width, height, label, &datum );
//     }
//     if( datum.channels() == 0 ||
//         datum.height() == 0 ||
//         datum.width() == 0 ) {
//       // LOG(ERROR) << "Datum details: channels : " << datum.channels()
//       //            << " Datum height " << datum.height() 
//       //            << " Datum width " << datum.width() ;
//       CHECK( false ) << " Issue with " << label;
//     }

//     std::string value;
//     datum.SerializeToString(&value);
//     leveldb_batch->Put( boost::to_string( label ), value );
//     label++;
//     if( label % batchSize == 0 ) {
//       // LOG(ERROR) << "Reached batch Size " << batchSize << " saving.";
//       saveLevelDb();
//       delete leveldb_batch;
//       leveldb_batch = new leveldb::WriteBatch();
//     }
//     return label - 1;
//   }
//   return label;
// }

void VideoDb::saveDb() {
  if (dbType == LEVELDB){
    leveldb_db->Write(leveldb::WriteOptions(), leveldb_batch);
  } else if (dbType == LMDB) {
  }
}

// void VideoDb::saveLevelDb() {
//   // LOG(ERROR) << "Saving current batch.";
//   leveldb_db->Write(leveldb::WriteOptions(), leveldb_batch);
// }

  // switch(dbType) {
  //   case LEVELDB: {
  //     break;
  //   }
  //   case LMDB: {
  //     break;
  //   }
  //   default: {
  //     CHECK(false) << "Unrecognized db type " << dbType;
  //   }
  // }

    // if (dbType == LEVELDB){
    // } else if (dbType == LMDB) {
    // }
