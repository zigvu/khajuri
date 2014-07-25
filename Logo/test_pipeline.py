#!/usr/bin/python

import glob, sys
import os, errno

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/../VideoReader'% baseScriptDir  )

from Pipeline import Pipeline
from CaffeNet import CaffeNet

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print 'Usage %s <config.yaml> <videoFileName> <outputDir>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  outputDir = sys.argv[3]

  pipeline = Pipeline(configFileName, videoFileName, outputDir)
  pipeline.run()
  # testNet = CaffeNet('/home/evan/Vision/temp/caffe_run/logo_video.prototxt', \
  #   '/home/evan/Vision/temp/caffe_run/caffe_logo_train_iter_5000', ["0","1"])
  # testNet.run_net(2, '/home/evan/Vision/temp/caffe_run/outputTest/leveldb/lUA7i4K2Sq8_leveldb_0')
