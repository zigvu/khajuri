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
  logger = config.logger

  amqp_url = config.mes_amqp_url
  serverQueueName = config.mes_q_vm2_kheer_development_heatmap_rpc_request

  logger.info("Heatmap rpc server started")

  heatmapDataHandler = HeatmapDataHandler(config)
  rpc = RpcServer(amqp_url, serverQueueName, heatmapDataHandler)


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1])
