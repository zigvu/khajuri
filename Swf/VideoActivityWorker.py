#!/usr/bin/env python
import time, json, pdb
import boto.swf.layer2 as swf
import logging, random
import os, errno
import ImageClassifier, VideoFrameExtractor, ConvertImageFormat, VideoEvaluate, S3Client, UIServer

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(process)-8d %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='VideoActivityWorker.log',
                    filemode='a')

class VideoActivityWorker( object ):

  def __init__( self, configFile, models, videoUrl, heartbeat ):
    self.configFile = configFile
    self.models = models
    self.videoUrl = videoUrl
    self.heartbeat = heartbeat

  def run(self):
      self.heartbeat.beat()
      logging.info( 'Running tasks' )

if __name__=="__main__":
  worker = VideoActivityWorker()
  worker.run()
