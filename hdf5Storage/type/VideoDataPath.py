import os

from config.Config import Config


class VideoDataPath(object):
  """Create paths for saving scores, clips"""

  def __init__(self, baseDir, videoId, chiaVersionId):
    """Initialize values"""
    self.base_path = os.path.join(baseDir, "%d" % videoId)
    Config.mkdir_p(self.base_path)

    self.scores_folder_path = os.path.join(self.base_path, "scores")
    self.scores_path = os.path.join(self.scores_folder_path,
                                    "%d.hdf5" % chiaVersionId)
    Config.mkdir_p(self.scores_folder_path)

    self.clips_folder_path = os.path.join(self.base_path, "clips")
    Config.mkdir_p(self.clips_folder_path)

  def __str__(self):
    return self.base_path
