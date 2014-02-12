""" Class describing all frames."""

from Error import FrameOutOfBoundsError

class Frame:
	"""The storage for a single frame. This class holds references 
	to all computation (e.g., edge detection) results on the frame."""
	def __init__(self, frameNumber):
		"""Initialize a single frame with frameNumber and define 
		references to hold all intermediate computation. Note all
		references are to be named FEAT_* and are to be 
		initialized to None.
		"""
		self.frameNumber = frameNumber
		self.FEAT_BLANKFRAME = None

	def __str__(self):
		"""Return a nice string representation of the object."""
		return str(self.frameNumber)

class FrameGroup:
	"""Container class representing a group of Frames that are 
	run through the plugin pipeline together in a DetectionStrand.

	Attributes:
		middleFrameNumber	-- frame number around which this group will be created
		config	 					-- configuration that provides group size and spacing between frames
	"""

	# TODO: check for out of bounds when video reading is complete	
	def __init__(self, middleFrameNumber, config):
		"""Initialize FrameGroup such that middleFrameNumber becomes the
		middle frame in the group. Spacing between frames and size of group
		determined by Config.
		"""
		self.frameList = []
		groupSize = config.getWindowFrameSize()
		spacingOfFrames = config.getWindowFrameSpacing()

		# Add to frame list:
		for i in range(-(groupSize-1)/2,(groupSize+1)/2):
			frameNumber = middleFrameNumber + i * spacingOfFrames
			if frameNumber < 0:
				# Check for bounds:
				raise FrameOutOfBoundsError(frameNumber, "FrameGroup init")
			else:
				self.frameList.append(Frame(frameNumber))


	def __iter__(self):
		"""Allow FrameGroup to behave like a regular list in for loops"""
		self.frameListSize = len(self.frameList)
		self.frameListIndex = 0
		return self

	def next(self):
		"""Get next Frame in iteration"""
		if self.frameListIndex >= self.frameListSize:
			raise StopIteration
		self.frameListIndex += 1
		return self.frameList[self.frameListIndex - 1]

	def __str__(self):
		"""Return a nice string representation of the object."""
		return "Frames: " + "; ".join(str(f) for f in self.frameList)

