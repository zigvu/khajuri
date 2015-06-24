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
  logger = config.logger

  config.total_num_of_patches = 543  # read this from config instead

  amqp_url = config.mes_amqp_url

  khajuriDataQueueName = config.mes_q_vm2_kahjuri_development_video_data
  kheerQueueName = config.mes_q_vm2_kheer_development_localization_request

  # this client sends data to kheer
  kheerRpcClient = RpcClient(amqp_url, kheerQueueName)

  logger.info("Starting RPC server to read video data")

  # this server runs in VM2 and listens to data from GPU1/GPU2
  videoDataHandler = VideoDataHandler(kheerRpcClient, config)
  rpc = RpcServer(amqp_url, khajuriDataQueueName, videoDataHandler)


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1])
