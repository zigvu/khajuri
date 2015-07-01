#!/usr/bin/env python

import sys

from config.Config import Config

from messaging.handlers.VideoDataHandler import VideoDataHandler
from messaging.infra.RpcServer import RpcServer
from messaging.infra.RpcClient import RpcClient

description = \
"""
This daemon will listen for video data storage requests and save score data 
to hdf5.

TODO: daemonize
"""


def process(configFileName):
  config = Config(configFileName)

  logger = config.logging.logger
  messagingCfg = config.messaging

  amqp_url = messagingCfg.amqpURL
  videoDataQueueName = messagingCfg.queues.videoData
  localizationRequestQueueName = messagingCfg.queues.localizationRequest

  # this client sends data to kheer
  kheerRpcClient = RpcClient(amqp_url, localizationRequestQueueName)

  logger.info("Starting RPC server to read video data")

  # this server runs in VM2 and listens to data from GPU1/GPU2
  videoDataHandler = VideoDataHandler(kheerRpcClient, config)
  rpc = RpcServer(amqp_url, videoDataQueueName, videoDataHandler)


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1])
