#!/usr/bin/python
import glob, sys
import os

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
  sys.path.append( dir )

from Logo.PipelineCore.ConfigReader import ConfigReader

from Logo.PipelineThread.CaffeThread import CaffeThread
from Logo.PipelineThread.PostProcessThread import PostProcessThread
from Logo.PipelineThread.VideoHeatmapThread import VideoHeatmapThread

if __name__ == '__main__':
  if len(sys.argv) < 6:
    print 'Usage %s <config.yaml> <videoFileName> <outputFolder> <prototxtFile> <modelFile>' % sys.argv[ 0 ]
    sys.exit(1)

  configFileName = sys.argv[1]
  videoFileName = sys.argv[2]
  outputFolder = sys.argv[3]
  prototxtFile = sys.argv[4]
  modelFile = sys.argv[5]

  configReader = ConfigReader(configFileName)
  leveldbFolder = os.path.join(outputFolder, configReader.sw_folders_leveldb)
  jsonFolder = os.path.join(outputFolder, configReader.sw_folders_json)
  numpyFolder = os.path.join(outputFolder, configReader.sw_folders_numpy)
  videoOutputFolder = os.path.join(outputFolder, configReader.sw_folders_video)

  # Run caffe
  caffeThread = CaffeThread(configFileName, videoFileName, leveldbFolder, jsonFolder)
  caffeThread.run()

  # Post process frames
  postProcessThread = PostProcessThread(configFileName, jsonFolder, numpyFolder)
  postProcessThread.run()

  # Create heatmap video if required
  if configReader.ci_saveVideoHeatmap:
	  videoHeatmapThread = VideoHeatmapThread(configFileName, \
	    videoFileName, jsonFolder, numpyFolder, videoOutputFolder)
	  videoHeatmapThread.run()
