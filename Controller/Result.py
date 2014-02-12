""" Class describing all results."""

from Error import ResultIncorrectStateError, ResultNotFoundError
from collections import OrderedDict
import json

class Result:
	"""Compute and store detection result when evaluating one frame
	with one plugin

	Attributes:
		frame 		- Frame to evaluate
		plugin		- Plugin to evaluate the frame with

	Constants:
		RESULT_EVALUATE_QUEUE 	- Allows for evaluating this frame/plugin combination
		RESULT_EVALUATE_END			- Prohibits evaluating this frame/plugin combination
		RESULT_EVALUATE_SUCCESS	- This frame/plugin combination evaluation succeeded
		RESULT_EVALUATE_FAIL		- This frame/plugin combination evaluation failed
	"""

	# ENUM equivalents:
	RESULT_EVALUATE_QUEUE = 'RESULT_EVALUATE_QUEUE'
	RESULT_EVALUATE_END = 'RESULT_EVALUATE_END'
	RESULT_EVALUATE_SUCCESS = 'RESULT_EVALUATE_SUCCESS'
	RESULT_EVALUATE_FAIL = 'RESULT_EVALUATE_FAIL'

	def __init__(self, frame, plugin):
		self.frame = frame
		self.plugin = plugin
		self.state = Result.RESULT_EVALUATE_QUEUE
		self.score = 0

	def process(self):
		if self.state != Result.RESULT_EVALUATE_QUEUE:
			raise ResultIncorrectStateError(
				self.frame, 
				self.plugin, 
				"Process request when not in RESULT_EVALUATE_QUEUE state. Received: " + self.state)
		self.score, self.processResult = self.plugin.process(self.frame)
		self.setState(Result.RESULT_EVALUATE_SUCCESS)
		return self.score, self.processResult
		# process the frame here and store & return processed value

	def getState(self):
		"""Get the state of the result"""
		return self.state

	def setState(self, newState):
		"""Set the state of the result"""
		self.state = newState

	def __str__(self):
		"""Return a nice string representation of the object."""
		return json.dumps({ 
					"Frame": str(self.frame),
					"Plugin": str(self.plugin),
					"Score": str(self.score),
					"State": str(self.state),
		})

class ResultGroup:
	"""Compute and store results of running a group of plugins through a 
	group of frames
	"""
	def __init__(self, frameGroup, pluginGroup):
		"""Construct a list of results"""
		self.resultList = []
		for plugin in pluginGroup:
			for frame in frameGroup:
				self.resultList.append(Result(frame, plugin))

	def updateFrameRunToEnd(self, result):
		"""Set state for this frame to not run any more plugins"""
		foundResults = []
		for cResult in self.resultList:
			if cResult.frame.frameNumber == result.frame.frameNumber:
				foundResults.append(cResult)
		if len(foundResults) <= 0:
			raise ResultNotFoundError(
				result.frame, 
				result.plugin, 
				"No matching results were found in result list")
		# update state of all non-evaluated plugins
		for cResult in foundResults:
			if cResult.getState() == Result.RESULT_EVALUATE_QUEUE:
				cResult.setState(Result.RESULT_EVALUATE_END)

	def updatePeerFrameRunToEnd(self, result):
		"""Set state of all peer of this frame to not run any more plugins"""
		foundResults = []
		for cResult in self.resultList:
			if cResult.frame.frameNumber != result.frame.frameNumber:
				foundResults.append(cResult)
		# update state of all non-evaluated plugins
		for cResult in foundResults:
			if cResult.getState() == Result.RESULT_EVALUATE_QUEUE:
				cResult.setState(Result.RESULT_EVALUATE_END)

	def getNextResultToEvaluate(self):
		"""Get next Result in list that still has RESULT_EVALUATE_QUEUE state"""
		for result in self.resultList:
			if result.getState() == Result.RESULT_EVALUATE_QUEUE:
				return result
		return None

	def __iter__(self):
		"""Allow ResultGroup to behave like a regular list in for loops"""
		self.resultListSize = len(self.resultList)
		self.resultListIndex = 0
		return self

	def next(self):
		"""Get next Result in iteration"""
		if self.resultListIndex >= self.resultListSize:
			raise StopIteration
		self.resultListIndex += 1
		return self.resultList[self.resultListIndex - 1]

	def __str__(self):
		"""Return a nice string representation of the object."""
		return "\n".join(str(result) for result in self.resultList)
