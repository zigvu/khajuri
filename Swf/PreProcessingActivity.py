#!/usr/bin/env python
import time
import boto.swf.layer2 as swf
import logging, json, yaml
import glob, sys, os
import os, tempfile, pdb
import VideoPipeline
from Controller.Config import Config
from Controller.DetectionStrand import DetectionStrandGroup
from plugins.model_eval.ModelDetectionHelper import ModelDetection
from yapsy.PluginManager import PluginManager
import S3Client

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(process)-8d %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='PreProcessingActivity.log',
                    filemode='a')

global config
config = yaml.load( open( "swf.yaml", "r" ) )
class PreProcessingActivity(swf.ActivityWorker):
  domain = config[ 'domain' ]
  version = config[ 'version' ]
  task_list = config[ 'task_list' ]
  models = {}
  pendingProcess = []

  def run( self ):
    logging.info( 'Polling for Tasks in Video Activity ...' )
    activity_task = self.poll()
    if 'activityId' in activity_task:
      jsonInput = json.loads( activity_task.get( 'input' ) )
      logging.info( 'Start Pre Process Tasks, input %s' % jsonInput )
      self.complete( result=activity_task.get( 'input' ) )

if __name__=="__main__":
  worker = PreProcessingActivity()
  while True:
    worker.run()
