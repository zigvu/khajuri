
class Machines(object):
  """Sets up machine related configs"""
  # declare constants
  GPU1 = 'GPU1'
  GPU2 = 'GPU2'
  VM = 'VM'

  def useGPU(self):
    use = False
    if (self.gpuDevices != None) and (len(self.gpuDevices) > 0):
      use = True
    return use

class GPUs(Machines):
  def __init__(self, mHash):
    """Initialize variables"""
    self.gpuDevices = mHash['gpu_devices']
    self.numCores = mHash['num_cores']

class GPU1(GPUs):
  def __init__(self, configHash):
    """Initialize variables"""
    GPUs.__init__(self, configHash['machines'][Machines.GPU1])

class GPU2(GPUs):
  def __init__(self, configHash):
    """Initialize variables"""
    GPUs.__init__(self, configHash['machines'][Machines.GPU2])

class VMs(Machines):
  def __init__(self, configHash):
    """Initialize variables"""
    self.gpuDevices = None
    mHash = configHash['machines'][Machines.VM]
    self.numCores = mHash['num_cores']
