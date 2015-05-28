#!/usr/bin/env python

from messaging.handlers.HeatmapDataHandler import HeatmapDataHandler
from messaging.infra.RpcServer import RpcServer

amqp_url = 'localhost'
serverQueueName = 'vm2.kheer.development.heatmap_rpc.request'

print "Heatmap rpc server started"

heatmapDataHandler = HeatmapDataHandler()
rpc = RpcServer( amqp_url, serverQueueName, heatmapDataHandler )
