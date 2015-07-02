
class Machines(object):
  """Sets up machine related configs"""
  # declare constants
  GPU1 = 'GPU1'
  GPU2 = 'GPU2'
  VM = 'VM'

  def __init__(self, configHash, mType):
    """Initialize variables"""
    self.mType = mType
    if self.mType == Machines.GPU1:
      mHash = configHash['machines'][Machines.GPU1]
      self.gpuDevices = mHash['gpu_devices']
      self.numCores = mHash['num_cores']

    elif self.mType == Machines.GPU2:
      mHash = configHash['machines'][Machines.GPU2]
      self.gpuDevices = mHash['gpu_devices']
      self.numCores = mHash['num_cores']

    elif self.mType == Machines.VM:
      mHash = configHash['machines'][Machines.VM]
      self.gpuDevices = None
      self.numCores = mHash['num_cores']

    else:
      raise RuntimeError("Machine not recognized: %s" % self.mType)

  def useGPU(self):
    use = False
    if (self.gpuDevices != None) and (len(self.gpuDevices) > 0):
      use = True
    return use
