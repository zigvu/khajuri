#!/usr/bin/env python

import logging, sys

from config.Config import Config

from messaging.handlers.VideoDataHandler import VideoDataHandler
from messaging.infra.RpcServer import RpcServer
from messaging.infra.RpcClient import RpcClient


def process( configFileName ):
  config = Config( configFileName )
  config.total_num_of_patches = 543 # read this from config instead

  amqp_url = config.mes_amqp_url

  khajuriDataQueueName = config.mes_q_vm2_kahjuri_development_video_data
  kheerQueueName = config.mes_q_vm2_kheer_development_localization_request

  logging.basicConfig(
    format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s PID:%(process)d - %(message)s',
    level=config.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  # this client sends data to kheer
  kheerRpcClient = RpcClient( amqp_url, kheerQueueName )

  logging.info( "Starting RPC server to read video data" )

  # this server runs in VM2 and listens to data from GPU1/GPU2
  videoDataHandler = VideoDataHandler( kheerRpcClient, config )
  rpc = RpcServer( amqp_url, khajuriDataQueueName, videoDataHandler )


if __name__ == '__main__':
  if len( sys.argv ) < 2:
    print 'Usage %s <config.yaml>' % sys.argv[ 0 ]
    sys.exit( 1 )
  process( sys.argv[ 1 ])
