""" Class describing a single detection strand."""

from Frame import FrameGroup
from Plugin import PluginGroup
from Result import ResultGroup

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
			
		# resultGroup now holds all computation results
		# Todo: JSONWriter(self.resultGroup)


class DetectionStrandGroup:
	"""Class to run a group of DetectionStrand.
	Attributes:
		videoFileName		- File name for the video
		config					- Configuration to use for this video
	"""
	def __init__(self, videoFileName, config):
		self.videoFileName = videoFileName
		self.config = config

