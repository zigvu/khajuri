#!/usr/bin/env python

import logging

from messaging.handlers.VideoDataHandler import VideoDataHandler
from messaging.infra.RpcServer import RpcServer
from messaging.infra.RpcClient import RpcClient

amqp_url = 'localhost'
khajuriDataQueueName = 'vm2.kahjuri.development.video_data'
kheerQueueName = 'vm2.kheer.development.localization.request'

# TODO: change based on config
logging.basicConfig(
  format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
  level=logging.INFO, datefmt="%Y-%m-%d--%H:%M:%S")

# this client sends data to kheer
kheerRpcClient = RpcClient( amqp_url, kheerQueueName )

logging.info( "Starting RPC server to read video data" )

# this server runs in VM2 and listens to data from GPU1/GPU2
videoDataHandler = VideoDataHandler( kheerRpcClient )
rpc = RpcServer( amqp_url, khajuriDataQueueName, videoDataHandler )
