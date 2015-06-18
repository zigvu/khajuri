#!/usr/bin/env python

import logging, sys

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

  amqp_url = config.mes_amqp_url
  serverQueueName = config.mes_q_vm2_kheer_development_heatmap_rpc_request

  logging.basicConfig(
      format=
      '{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
      level=config.log_level,
      datefmt="%Y-%m-%d--%H:%M:%S")

  logging.info("Heatmap rpc server started")

  heatmapDataHandler = HeatmapDataHandler(config)
  rpc = RpcServer(amqp_url, serverQueueName, heatmapDataHandler)


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1])
