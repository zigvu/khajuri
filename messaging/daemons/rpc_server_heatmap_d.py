#!/usr/bin/env python

import logging

from messaging.handlers.HeatmapDataHandler import HeatmapDataHandler
from messaging.infra.RpcServer import RpcServer

amqp_url = 'localhost'
serverQueueName = 'vm2.kheer.development.heatmap_rpc.request'

# TODO: change based on config
logging.basicConfig(
  format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
  level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S")

logging.info( "Heatmap rpc server started" )

heatmapDataHandler = HeatmapDataHandler()
rpc = RpcServer( amqp_url, serverQueueName, heatmapDataHandler )
