#!/usr/bin/env python

import numpy as np

from hdf5Storage.type.FrameData import FrameData
from messaging.type.Headers import Headers
from messaging.infra.RpcClient import RpcClient
from messaging.infra.Pickler import Pickler

# TODO: replace so that it works across machines
amqp_url = 'localhost'
serverQueueName = 'vm2.kahjuri.development.video_data'

rpcClient = RpcClient( amqp_url, serverQueueName )
headers = Headers.videoStorageSave( 2, 1 )


fd = FrameData(1, 1, 1)
fd.scores = np.ones((1,1))
print "Pushing score data - 1"
rpcClient.call(headers, Pickler.pickle(fd))

fd = FrameData(1, 1, 2)
fd.scores = np.ones((2,2))
print "Pushing score data - 2"
rpcClient.call(headers, Pickler.pickle(fd))

fd = FrameData(1, 1, 3)
fd.scores = np.ones((3,3))
print "Pushing score data - 3"
rpcClient.call(headers, Pickler.pickle(fd))
