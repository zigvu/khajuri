#!/usr/bin/env python

import multiprocessing, time, os, logging
import math, sys, glob, json, shutil

from config.Config import Config

from hdf5Storage.type.VideoDataPath import VideoDataPath

from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient

def process( configFileName, videoFolder, videoId ):
  config = Config( configFileName )
  baseFolder = config.hdf5_base_folder
  videoClipsMapFilename = os.path.join( videoFolder, config.hdf5_video_clips_map_filename )
  amqp_url = config.mes_amqp_url
  serverQueueName = config.mes_q_vm2_kheer_development_clip_id_request

  videoDataPath = VideoDataPath( baseFolder, videoId, 0 )
  clipsFolderPath = videoDataPath.clips_folder_path

  # STEP 1:
  # this client needs to be defined at the begining of
  # video processing pipeline - this is the mechanism for communication
  # between GPU1/GPU2 and VM1/VM2
  rpcClient = RpcClient( amqp_url, serverQueueName )

  # STEP 2:
  # as each clip is created, we get a clip_id from kheer
  # and use this to push the newly created clip to VM2
  # note: currently, no such queue exists - files are copied instead
  videoClipsMap = json.load( open( videoClipsMapFilename, "r" ) )
  sortedClipsIds = sorted([int(x) for x in videoClipsMap.keys()])

  for qId in sortedClipsIds:
    vData = videoClipsMap[str(qId)]
    headers = Headers.clipId( videoId )
    message = {
      'video_id': videoId,
      'frame_number_start': vData[ 'frame_number_start' ],
      'frame_number_end': vData[ 'frame_number_end' ]
    }
    response = json.loads( rpcClient.call( headers, json.dumps( message ) ) )
    srcVideoFile = os.path.join( videoFolder, vData[ 'clip_filename' ] )
    dstVideoFile = os.path.join( clipsFolderPath, "%s.mp4" % response[ 'clip_id' ] )
    shutil.copy(srcVideoFile, dstVideoFile)
    print "Adding video: %s" % ( dstVideoFile )

if __name__ == '__main__':
  if len( sys.argv ) < 4:
    print 'Usage %s <config.yaml> <videoFolder> <videoId>' % sys.argv[ 0 ]
    sys.exit( 1 )
  process( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ) )
