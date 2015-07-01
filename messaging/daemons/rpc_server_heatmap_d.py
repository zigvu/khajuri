#!/usr/bin/env python

import sys

from config.Config import Config

from messaging.handlers.HeatmapDataHandler import HeatmapDataHandler
from messaging.infra.RpcServer import RpcServer

description = \
"""
This daemon will listen for heatmap data requests and serve them

TODO: daemonize
"""


def process(configFileName):
  config = Config(configFileName)

  logger = config.logging.logger
  messagingCfg = config.messaging

  amqp_url = messagingCfg.amqpURL
  serverQueueName = messagingCfg.queues.heatmapRequest

  logger.info("Heatmap rpc server started")

  heatmapDataHandler = HeatmapDataHandler(config)
  rpc = RpcServer(amqp_url, serverQueueName, heatmapDataHandler)


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1])
