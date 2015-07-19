
class Jobs(object):
  """Sets up jobs related configs"""
  # declare constants
  PROCESS_VIDEO = 'process_video'
  HEATMAP_DAEMON = 'heatmap_daemon'
  HDF5_WRITER_DAEMON = 'hdf5_writer_daemon'
  LOG_WRITER_DAEMON = 'log_writer_daemon'

  def __init__(self, configHash, jobType):
    """Initialize variables"""
    self.jobType = jobType

    if self.jobType == Jobs.PROCESS_VIDEO:
      jobHash = configHash['jobs'][Jobs.PROCESS_VIDEO]

      self.videoId = jobHash['video_id']
      self.videoFileName = jobHash['video_file_name']
      self.chiaVersionId = jobHash['chia_version_id']
      self.kheerJobId = jobHash['kheer_job_id']
      self.zigvuJobId = jobHash['zigvu_job_id']

    elif self.jobType == Jobs.HEATMAP_DAEMON:
      jobHash = configHash['jobs'][Jobs.HEATMAP_DAEMON]

      self.zigvuJobId = jobHash['zigvu_job_id']

    elif self.jobType == Jobs.HDF5_WRITER_DAEMON:
      jobHash = configHash['jobs'][Jobs.HDF5_WRITER_DAEMON]

      self.zigvuJobId = jobHash['zigvu_job_id']

    elif self.jobType == Jobs.LOG_WRITER_DAEMON:
      jobHash = configHash['jobs'][Jobs.LOG_WRITER_DAEMON]

      self.zigvuJobId = jobHash['zigvu_job_id']

    else:
      raise RuntimeError("Job type not recognized: %s" % self.jobType)

  def getLogExtraParams(self):
    if self.jobType == Jobs.PROCESS_VIDEO:
      return { 
        'kheerJobId': self.kheerJobId,
        'zigvuJobId': self.zigvuJobId
      }
    else:
      return { 'zigvuJobId': self.zigvuJobId }
