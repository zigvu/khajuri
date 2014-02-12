""" Class describing a single detection strand."""

from Frame import FrameGroup
from Plugin import PluginGroup
from Result import ResultGroup
import VideoReader
import multiprocessing
from multiprocessing.pool import ThreadPool
import time, os, json

class DetectionStrand:
	"""Class to run a group of frames through a group of plugins.
	Attributes:
		resultGroup 		- Collection of results for frame/plugin evaluation
		config					- Configuration to use for this strand

	Constants:
		DETECTIONSTRAND_TYPE_INTERVAL 	- Indicates that this strand is a regular interval strand
		DETECTIONSTRAND_TYPE_WINDOW 		- Indicates that this strand is a windowing strand
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

	def process(self):
		"""Run the detection strand and save subsequent resultGroup"""
		runAdditionalStrands = False
		result = self.resultGroup.getNextResultToEvaluate()
		while result != None:
			# first, process the result
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
		videoFileName		- File name for the video
		config					- Configuration to use for this video
	"""
	def __init__(self, videoFileName, config):
		self.videoFileName = videoFileName
		self.config = config
		self.videoFrameReader = VideoReader.VideoFrameReader( 40, 40, self.videoFileName )
		self.config.videoFrameReader = self.videoFrameReader
		self.config.baseFrameFolder = os.path.join( os.path.dirname( self.videoFileName ),  "frames" )
		if not os.path.exists( self.config.baseFrameFolder ):
			os.makedirs( self.config.baseFrameFolder )
		self.videoFrameReader.generateFrames()

	def runVidPipe(self):
	        results = []
	        second = 0
		fps = self.videoFrameReader.fps
		time.sleep( 1 )
		while not self.videoFrameReader.eof:
			ds = DetectionStrand( int( ( second * fps ) + fps/2.0 ), self.config )
			ds.process()
			second += 1
			results.extend( ds.resultGroup )
		self.videoFrameReader.waitForEOF()
		self.resultsByPlugin = {}
		for result in results:
			if not self.resultsByPlugin.get( result.plugin.name ):
				self.resultsByPlugin[ result.plugin.name ] = []
			self.resultsByPlugin[ result.plugin.name ].append( result )
		for plugin in self.resultsByPlugin.keys():
			self.saveResultToFile( plugin, self.resultsByPlugin[ plugin ] )
	
	def saveResultToFile( self, pluginName, results ):
		resultsFolder = os.path.join( os.path.dirname( self.videoFileName ), "results" )
		if not os.path.exists( resultsFolder ):
			os.makedirs( resultsFolder )
		resultsFileName = os.path.join( resultsFolder, "%s.json" % pluginName )
		jsonResult = {}
		for r in results:
			jsonResult[ "%s" % r.frame ] = { "Score":"%s" % r.score, "State":"%s" % r.state }
		json.dump( jsonResult, open( resultsFileName, "w" ) )
