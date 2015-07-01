import h5py

from hdf5Storage.type.FrameData import FrameData
from hdf5Storage.type.VideoDataPath import VideoDataPath


class VideoDataReader(object):
  """Read video data from hdf5"""

  def __init__(self, config, videoId, chiaVersionId):
    """Initialize values"""
    self.config = config

    self.logger = self.config.logging.logger
    self.storageCfg = self.config.storage
    self.slidingWindowCfg = self.config.slidingWindow
    self.caffeInputCfg = self.config.caffeInput

    self.baseFolder = self.storageCfg.hdf5BaseFolder
    self.frameDensity = self.slidingWindowCfg.sw_frame_density
    self.videoFrameNumberStart = self.caffeInputCfg.ci_videoFrameNumberStart

    self.videoId = videoId
    self.chiaVersionId = chiaVersionId

    # create reader for hdf5 file
    self.videoDataPath = VideoDataPath(
        self.baseFolder, self.videoId, self.chiaVersionId)
    self.videoScoresFile = h5py.File(self.videoDataPath.scores_path, 'r')
    self.createScoresDataSet()

  def createScoresDataSet(self):
    """
    The patch scores are stored in a 3-d numpy array
    1 dim => patches
    2 dim => classes
    3 dim => frame number
    """
    self.scoresDataSet = self.videoScoresFile['scores']
    if ((self.videoId != int(self.scoresDataSet.attrs['video_id'])) or
        (self.chiaVersionId !=
         int(self.scoresDataSet.attrs['chia_version_id']))):
      raise RuntimeError('VideoId or ChiaVersionId does not match')

  def getFrameData(self, frameNumber):
    """Read frame data from HDF5
    Return in FrameData data structure
    """
    self.logger.debug(
        "Get frame data for: VideoId: %d, ChiaVersionId: %d, FrameNumber: %d" %
        (self.videoId, self.chiaVersionId, frameNumber))
    fn = (frameNumber - self.videoFrameNumberStart) / self.frameDensity
    frameData = FrameData(self.videoId, self.chiaVersionId, fn)
    frameData.scores = self.scoresDataSet[:, :, fn]
    return frameData

  def close(self):
    """Close file"""
    self.videoScoresFile.close()

  # context manager helpers to enable usage of this class in `with` keyword
  def __enter__(self):
    return self

  def __exit__(self, exception_type, exception_val, trace):
    self.close()
