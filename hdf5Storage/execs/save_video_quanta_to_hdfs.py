#!/usr/bin/env python

import os
import sys, json, shutil

from config.Config import Config

from hdf5Storage.type.VideoDataPath import VideoDataPath

from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient

description = \
"""
This script will save video clips to VM1/VM2.
This script is intended to be run in VM1/VM2 machines and will ask for
clip IDs to kheer through RabbitMq.
It is expected that a corresponding consumer daemon is running in kheer to
provide clip Ids.

TODO: make it so that we can run this script from GPU1/GPU2.
"""


def process(configFileName, videoFolder, videoId):
  config = Config(configFileName)

  logger = config.logging.logger
  messagingCfg = config.messaging
  storageCfg = config.storage

  baseFolder = storageCfg.hdf5BaseFolder
  videoClipsMapFilename = os.path.join(
      videoFolder, storageCfg.hdf5VideoClipsMapFilename)
  amqp_url = messagingCfg.amqpURL
  serverQueueName = messagingCfg.queues.clipIdRequest

  videoDataPath = VideoDataPath(baseFolder, videoId, 0)
  clipsFolderPath = videoDataPath.clips_folder_path

  # STEP 1:
  # this client needs to be defined at the begining of
  # video processing pipeline - this is the mechanism for communication
  # between GPU1/GPU2 and VM1/VM2
  rpcClient = RpcClient(amqp_url, serverQueueName)

  # STEP 2:
  # as each clip is created, we get a clip_id from kheer
  # and use this to push the newly created clip to VM2
  # note: currently, no such queue exists - files are copied instead
  videoClipsMap = json.load(open(videoClipsMapFilename, "r"))
  sortedClipsIds = sorted([int(x) for x in videoClipsMap.keys()])

  for qId in sortedClipsIds:
    vData = videoClipsMap[str(qId)]
    headers = Headers.clipId(videoId)
    message = {
        'video_id': videoId,
        'frame_number_start': vData['frame_number_start'],
        'frame_number_end': vData['frame_number_end']
    }
    response = json.loads(rpcClient.call(headers, json.dumps(message)))
    srcClipFile = os.path.join(videoFolder, vData['clip_filename'])
    dstClipFile = os.path.join(clipsFolderPath, "%s.mp4" % response['clip_id'])
    shutil.copy(srcClipFile, dstClipFile)
    logger.info("Adding clip: %s" % dstClipFile)


if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <videoFolder> <videoId>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1], sys.argv[2], int(sys.argv[3]))
