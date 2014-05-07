""" Class describing a single detection strand."""

from Controller.Frame import FrameGroup
from Controller.PluginGroup import PluginGroup
from Controller.Result import ResultGroup
from Controller.TempFS import TempFileFS
from VideoReader import VideoReader
import multiprocessing
from multiprocessing.pool import ThreadPool
import time, os, json

class DetectionStrand:
  """Class to run a group of frames through a group of plugins.
  Attributes:
    resultGroup     - Collection of results for frame/plugin evaluation
    config          - Configuration to use for this strand

  Constants:
    DETECTIONSTRAND_TYPE_INTERVAL   - Indicates that this strand is a regular interval strand
    DETECTIONSTRAND_TYPE_WINDOW     - Indicates that this strand is a windowing strand
  """
  # ENUM equivalents:
  DETECTIONSTRAND_TYPE_INTERVAL = 'DETECTIONSTRAND_TYPE_INTERVAL'
  DETECTIONSTRAND_TYPE_WINDOW = 'DETECTIONSTRAND_TYPE_WINDOW'

  def __init__(self, middleFrameNumber, config, strandType = None):
    frameGroup = FrameGroup(middleFrameNumber, config)
    pluginGroup = PluginGroup(config)
    self.resultGroup = ResultGroup(frameGroup, pluginGroup)
    self.config = config
    # set the type of strand
    if strandType == None:
      self.strandType = DetectionStrand.DETECTIONSTRAND_TYPE_INTERVAL
    else:
      self.strandType = strandType

  def process(self, activityWorker):
    """Run the detection strand and save subsequent resultGroup"""
    runAdditionalStrands = False
    result = self.resultGroup.getNextResultToEvaluate()
    while result != None:
      # first, process the result
      activityWorker.heartbeat()
      processResult, processDecision = result.process()
      # if the plugin is to let through only 1 frame:
      if result.plugin.name == self.config.getPluginClassNameForSelectingSingleFrame():
        self.resultGroup.updatePeerFrameRunToEnd(result)
      # if decision is to not let other plugins to run on this frame:
      if not processDecision:
        self.resultGroup.updateFrameRunToEnd(result)
      # if any of the model detection is positive, set runAdditionalStrands
      if (result.plugin.name == self.config.getPluginClassNameForModelDetection()) \
          and (not runAdditionalStrands) \
          and (processDecision):
        runAdditionalStrands = True
      # get next result to iterate over
      result = self.resultGroup.getNextResultToEvaluate()
    # logic to create next detection strand if necessary
    if (self.strandType == DetectionStrand.DETECTIONSTRAND_TYPE_INTERVAL) \
        and runAdditionalStrands:
      # TODO: insert into DetectionStrandGroup
      pass

class DetectionStrandGroup:
  """Class to run a group of DetectionStrand.
  Attributes:
    videoFileName   - File name for the video
    config          - Configuration to use for this video
  """
  def __init__(self, config ):
    self.config = config

  def runVidPipe(self, videoFileName, activityWorker):
    activityWorker.heartbeat()
    self.videoFileName = videoFileName
    self.videoFrameReader = VideoReader.VideoFrameReader( 40, 40, self.videoFileName )
    self.config.getPluginConfig("FrameExtraction")["videoFrameReader"] = self.videoFrameReader
    self.videoFrameReader.generateFrames()
    activityWorker.heartbeat()
    results = []
    second = 0
    fps = self.videoFrameReader.fps
    time.sleep( 1 )
    while not self.videoFrameReader.eof:
      with TempFileFS( self.videoFileName ) as ramFSDir:
        baseFrameFolder = os.path.join( ramFSDir,  "frames" )
        if not os.path.exists( baseFrameFolder ):
          os.makedirs( baseFrameFolder )
          self.config.getPluginConfig("FrameExtraction")["baseFrameFolder"] = baseFrameFolder
        activityWorker.heartbeat()
        ds = DetectionStrand( int( ( second * fps ) + fps/2.0 ), self.config )
        ds.process( activityWorker )
        second += 1
        results.extend( ds.resultGroup )
    self.videoFrameReader.waitForEOF()
    resultsDict = {}
    for r in results:
      frameId = str( r.frame )
      if not resultsDict.get( frameId ):
        resultsDict[ frameId ] = { "filters": [ ], "models": [ ] }
      if str( r.plugin ).startswith( "Model" ):
        resultsDict[ frameId ][ "models" ].append( { "ModelID": "%s" % r.plugin.modelId,
                    "state" : "%s" % r.state,
                    "score" : "%s" % r.score } )
      else:
        resultsDict[ frameId ][ "filters" ].append( { "FilterName": "%s" % r.plugin,
                    "state" : "%s" % r.state,
                    "score" : "%s" % r.score } )
    resultsFileName = os.path.join( os.path.dirname( self.videoFileName ), "%s.json" % self.config.getCampaignId() )
    json.dump( resultsDict, open( resultsFileName, "w" ), sort_keys=True, indent=2 )
