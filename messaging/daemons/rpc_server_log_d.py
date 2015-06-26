#!/usr/bin/env python

import sys

from config.Config import Config

from messaging.handlers.LogHandler import LogHandler
from messaging.infra.RpcServer import RpcServer

description = \
"""
This daemon will listen for log storage requests and send them to
Graylog2 logging system.

TODO: daemonize
"""


def process(configFileName):
  config = Config(configFileName)
  logger = config.logger

  amqp_url = config.mes_amqp_url
  serverQueueName = config.mes_q_vm2_khajuri_development_log

  logger.info("Starting RPC server to read logs")

  # this server runs in VM2 and listens to logs from GPU1/GPU2
  logHandler = LogHandler(config)
  rpc = RpcServer(amqp_url, serverQueueName, logHandler)


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[0]
    print description
    sys.exit(1)
  process(sys.argv[1])
