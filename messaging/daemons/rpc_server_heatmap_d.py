#!/usr/bin/env python

import sys
from multiprocessing import Process

from Logo.PipelineCore.LogConsolidator import LogConsolidator

from config.Config import Config

from messaging.handlers.HeatmapDataHandler import HeatmapDataHandler
from messaging.infra.RpcServer import RpcServer

description = \
"""
This daemon will listen for heatmap data requests and serve them

TODO: daemonize
"""

config = None

def runLogConsolidator():
  """Consolidate log from multiple processes"""
  logConsolidator = LogConsolidator(config)
  logConsolidator.startConsolidation()

def process(configFileName):
  global config
  config = Config(configFileName)
  loggingCfg = config.logging
  messagingCfg = config.messaging

  # # Logging infrastructure
  logConsolidatorProcess = Process(target=runLogConsolidator, args=())
  logConsolidatorProcess.start()

  logger = loggingCfg.logger

  amqp_url = messagingCfg.amqpURL
  serverQueueName = messagingCfg.queues.heatmapRequest

  logger.info("Heatmap rpc server started")

  heatmapDataHandler = HeatmapDataHandler(config)
  rpc = RpcServer(amqp_url, serverQueueName, heatmapDataHandler)

  # NOTE: since this executable is run as a daemon, it is expected
  # to never complete - hence no need to join log queue

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1])
