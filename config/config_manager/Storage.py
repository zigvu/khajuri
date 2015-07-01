
class Storage(object):
  """Sets up storage related configs"""
  def __init__(self, configHash):
    """Initialize variables"""
    storHash = configHash['storage']

    self.enableJsonReadWrite = storHash['json_read_write'] == True
    self.enableHdf5ReadWrite = storHash['hdf5_read_write'] == True

    localHash = storHash['local']
    self.baseDbFolder = localHash['base_db_folder']
    self.jsonFolder = localHash['json_folder']

    hdf5Hash = storHash['hdf5']
    self.hdf5BaseFolder = hdf5Hash['hdf5_base_folder']
    self.hdf5ClipFrameCount = 1024
    self.hdf5VideoClipsMapFilename = 'clips_map.json'
