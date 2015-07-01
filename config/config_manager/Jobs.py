
class Jobs(object):
  """Sets up jobs related configs"""
  # declare constants
  PROCESS_VIDEO = 'process_video'
  HEATMAP_DAEMON = 'heatmap_daemon'
  HDF5_WRITER_DAEMON = 'hdf5_writer_daemon'

  def getLogExtraParams(self):
    raise NotImplementedError("Class has not implemented logging message")

class ProcessVideoJob(Jobs):
  """Sets up jobs related configs"""
  def __init__(self, configHash):
    """Initialize variables"""
    processVideoJob = configHash['jobs'][Jobs.PROCESS_VIDEO]

    self.videoId = processVideoJob['video_id']
    self.videoFileName = processVideoJob['video_file_name']
    self.chiaVersionId = processVideoJob['chia_version_id']

    self.kheerJobId = processVideoJob['kheer_job_id']
    self.zigvuJobId = processVideoJob['zigvu_job_id']

  def getLogExtraParams(self):
    return { 
      'kheerJobId': self.kheerJobId,
      'zigvuJobId': self.zigvuJobId
    }



class HeatmapDaemonJob(Jobs):
  """Sets up jobs related configs"""
  def __init__(self, configHash):
    """Initialize variables"""
    heatmapDaemonJob = configHash['jobs'][Jobs.HEATMAP_DAEMON]

    self.zigvuJobId = heatmapDaemonJob['zigvu_job_id']

  def getLogExtraParams(self):
    return { 'zigvuJobId': self.zigvuJobId }



class HDF5WriterDaemonJob(Jobs):
  """Sets up jobs related configs"""
  def __init__(self, configHash):
    """Initialize variables"""
    hdf5WriterDaemonJob = configHash['jobs'][Jobs.HDF5_WRITER_DAEMON]

    self.zigvuJobId = hdf5WriterDaemonJob['zigvu_job_id']

  def getLogExtraParams(self):
    return { 'zigvuJobId': self.zigvuJobId }

