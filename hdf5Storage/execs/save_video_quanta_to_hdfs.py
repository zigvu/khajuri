#!/usr/bin/env python

import multiprocessing, time, os, logging
import math, sys, glob, json, shutil

from config.Config import Config

from hdf5Storage.type.VideoDataPath import VideoDataPath

from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient

def process( configFileName, videoFolder, videoId ):
  # TODO: get from config file

  # config = Config( configFileName )
  # baseFolder = config.hdf5_base_folder
  # numFrameInQuanta = config.hdf5_quanta_frame_count
  # videoQuantaMapFilename = os.path.join( videoFolder, config.video_quanta_map_filename )
  baseFolder = '/home/evan/RoR/kheer/public/data'
  numFrameInQuanta = 1024
  videoQuantaMapFilename = os.path.join( videoFolder, 'quanta_map.json' )

  videoDataPath = VideoDataPath( baseFolder, videoId, 0 )
  quantaFolderPath = videoDataPath.quanta_folder_path

  # TODO: get from config file
  amqp_url = 'localhost'
  serverQueueName = 'vm2.kheer.development.video_id.request'


  # STEP 1:
  # this client needs to be defined at the begining of
  # video processing pipeline - this is the mechanism for communication
  # between GPU1/GPU2 and VM1/VM2
  rpcClient = RpcClient( amqp_url, serverQueueName )

  # STEP 2:
  # as each quanta is created, we get a quanta id from kheer
  # and use this to push the newly created quanta to VM2
  # note: currently, no such queue exists - files are copied instead
  videoQuantaMap = json.load( open( videoQuantaMapFilename, "r" ) )
  sortedQuantaIds = sorted([int(x) for x in videoQuantaMap.keys()])

  for qId in sortedQuantaIds:
    vData = videoQuantaMap[str(qId)]
    headers = Headers.quantaId( videoId )
    message = {
      'video_id': videoId,
      'frame_number_start': vData[ 'frame_number_start' ],
      'frame_number_end': vData[ 'frame_number_end' ]
    }
    response = json.loads( rpcClient.call( headers, json.dumps( message ) ) )
    srcVideoFile = os.path.join( videoFolder, vData[ 'video_filename' ] )
    dstVideoFile = os.path.join( quantaFolderPath, "%s.mp4" % response[ 'quanta_id' ] )
    shutil.copy(srcVideoFile, dstVideoFile)
    print "Adding video: %s" % ( dstVideoFile )

if __name__ == '__main__':
  if len( sys.argv ) < 4:
    print 'Usage %s <config.yaml> <videoFolder> <videoId>' % sys.argv[ 0 ]
    sys.exit( 1 )
  process( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ) )
