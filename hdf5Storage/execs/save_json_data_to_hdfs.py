#!/usr/bin/env python

import time, os, logging
import sys, glob, json
import numpy as np

from config.Config import Config
from postprocessing.task.JsonReader import JsonReader

from hdf5Storage.type.FrameData import FrameData

from messaging.infra.Pickler import Pickler
from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient

def process( configFileName, jsonFolder, videoId, chiaVersionId ):
  config = Config( configFileName )

  # TODO: get from config file
  config.videoId = 1 # strangely, without this, JsonReader will break
  config.total_num_of_patches = 543 # read this from config instead
  jsonReader = JsonReader( config, None )


  amqp_url = config.mes_amqp_url
  serverQueueName = config.mes_q_vm2_kahjuri_development_video_data

  # STEP 1:
  # this client needs to be defined at the begining of
  # video processing pipeline - this is the mechanism for communication
  # between GPU1/GPU2 and VM1/VM2
  rpcClient = RpcClient( amqp_url, serverQueueName )

  # STEP 2:
  # need to inform VM1/VM2 that a new video processing is begining
  # for now, we are the originator of config object - this will change
  # once we have a more robust config manager
  message = Pickler.pickle( config )
  headers = Headers.videoStorageStart( videoId, chiaVersionId )
  response = json.loads( rpcClient.call( headers, message ) )

  # STEP 3:
  # as frames are processed, they need to be pushed to the rpcClient
  # note: order of frame processing doesn't matter
  jsonFolderFiles = glob.glob( os.path.join( jsonFolder, "*json" ) )
  for jsonFileName in jsonFolderFiles:
    print "Adding: %s" % jsonFileName
    frame, classIds = jsonReader( jsonFileName )

    # extract data that needs to pass through network
    frameData = FrameData( videoId, chiaVersionId, frame.frameNumber )
    # get prob scores for zdist 0
    frameData.scores = frame.scores[ 0 ][ :, :, 0 ].astype(np.float16)
    # get localizations for all zdist
    frameData.localizations = frame.localizations

    # send to storage queue
    message = Pickler.pickle( frameData )
    headers = Headers.videoStorageSave( videoId, chiaVersionId )
    response = json.loads( rpcClient.call( headers, message ) )

    # STEP 4:
    # clip needs to be pushed to another queue
    # the mechanism is TBD - use another executable for now

  # STEP 5:
  # need to inform VM1/VM2 that a new video processing is ending
  message = Pickler.pickle( {} )
  headers = Headers.videoStorageEnd( videoId, chiaVersionId )
  response = json.loads( rpcClient.call( headers, message ) )


if __name__ == '__main__':
  if len( sys.argv ) < 5:
    print 'Usage %s <config.yaml> <jsonFolder> <videoId> <chiaVersionId>' % sys.argv[ 0 ]
    sys.exit( 1 )
  process( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ), int( sys.argv[ 4 ] ) )
