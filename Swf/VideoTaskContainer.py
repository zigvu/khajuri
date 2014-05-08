#!/usr/bin/env python
import multiprocessing
import shlex, subprocess
import time
import boto.swf.layer2 as swf
import logging, json, yaml
import glob, sys
import os, tempfile, pdb
from multiprocessing import Process
import VideoPipeline
from Controller.Config import Config
from Controller.DetectionStrand import DetectionStrandGroup
from plugins.model_eval.ModelDetectionHelper import ModelDetection
from yapsy.PluginManager import PluginManager
import S3Client

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(process)-8d %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='VideoTaskContainer.log',
                    filemode='a')

global config
config = yaml.load( open( "swf.yaml", "r" ) )
def startPlugins( activityWorker, dsg, jsonInput ):
  # Load the plugins from the plugin directory.
  config = yaml.load( open( "swf.yaml", "r" ) )
  manager = PluginManager()
  pluginDir = os.path.dirname(os.path.realpath(__file__))
  manager.setPluginPlaces([ os.path.join( pluginDir, "plugins" ) ] )
  manager.collectPlugins()
  params = {}
  params[ 'activity.worker' ] = activityWorker
  params[ 'dsg' ] = dsg
  params[ config[ 'videoUrlKey' ] ] = jsonInput[ config[ 'videoUrlKey' ] ]
  params[ config[ 'videoIdKey' ] ] = jsonInput[ config[ 'videoIdKey' ] ]

  # Loop round the plugins and run them
  plugins = manager.getAllPlugins()
  pluginsInOrder = {}
  for plugin in plugins:
      myOrder = plugin.details.get( 'Documentation', 'Order' )
      pluginsInOrder[ myOrder ] = plugin

  for key in sorted( pluginsInOrder.keys() ):
      plugin = pluginsInOrder[ key ]
      plugin.plugin_object.run( params )

dsg = None
class VideoTaskContainer(swf.ActivityWorker):
  domain = config[ 'domain' ]
  version = config[ 'version' ]
  task_list = config[ 'task_list' ]
  models = {}
  pendingProcess = []

  def run( self ):
    global dsg
    global config
    def aliveCount():
      count = 0
      for p in self.pendingProcess:
        if p.is_alive():
          count += 1
        else:
           p.join()
      return count

    aliveProcess = aliveCount()
    logging.info( 'Alive Count is %s' % aliveProcess )
    if aliveProcess >= multiprocessing.cpu_count():
      logging.info( 'Alive is high, sleeping %s' % ( 10 - aliveProcess ) )
      time.sleep( 10 - aliveProcess )
      return

    logging.info( 'Polling for Tasks in Video Activity ...' )
    activity_task = self.poll()
    if 'activityId' in activity_task:
      jsonInput = json.loads( activity_task.get( 'input' ) )
      logging.info( 'Start Tasks, input %s' % jsonInput )

      if not dsg:
        # From the config.yaml file, get the list of models
        # Download the models
        # Create all models to pass to VideoActivityWorker
        # From JsonInput, get the config.yaml file url
        videoId = jsonInput[ config[ 'videoIdKey' ] ]
        myconn = S3Client.ZigVuS3Connection()
        # Download the config file and create config object
        config = Config( myconn.getVideoConfigFile( videoId, config[ 'bucketname' ] ) )
        for plugin in config.getPluginClassNames():
          if plugin.startswith( "Model" ):
            modelConfig = config.getPluginConfig( plugin )
            modelDet = ModelDetection(modelConfig)
        dsg = DetectionStrandGroup( config )
      
      #startPlugins( self, dsg, jsonInput )
      p = Process( target=startPlugins,
                      args = ( self, dsg, jsonInput ) )
      p.start()
      self.pendingProcess.append( p )

if __name__=="__main__":
  worker = VideoTaskContainer()
  while True:
    worker.run()
