import os, errno
import yaml, json
import scipy.ndimage as ndimage
import logging

class ConfigReader:
  """Reads YAML config file and allows easy accessor to config attributes"""
  def __init__(self, configFileName):
    """Initlize config from YAML file"""
    config = yaml.load(open(configFileName, "r"))

    # Logging
    self.log_level = logging.DEBUG
    if config['log_level'] == 'INFO':
      self.log_level = logging.INFO
    if config['log_level'] == 'ERROR':
      self.log_level = logging.ERROR

    # Sliding window creation:
    slidingWindow = config['sliding_window']
    sw_folders = slidingWindow['folders']
    self.sw_folders_frame = sw_folders['frame_output']
    self.sw_folders_patch = sw_folders['patch_output']
    self.sw_folders_annotation = sw_folders['annotation_output']
    self.sw_folders_leveldb = sw_folders['levedb_output']

    self.sw_frame_density = int(slidingWindow['frame_density'])
    self.sw_patchWidth = int(slidingWindow['output_width'])
    self.sw_patchHeight = int(slidingWindow['output_height'])
    self.sw_xStride = int(slidingWindow['x_stride'])
    self.sw_yStride = int(slidingWindow['y_stride'])
    
    self.sw_scales = []
    sw_temp_scales = slidingWindow['scaling']
    for sw_scale in sw_temp_scales:
      self.sw_scales = self.sw_scales + [float(sw_scale)]

    # Caffe input
    caffeInput = config['caffe_input']
    self.ci_modelFile = caffeInput['model_file']
    self.ci_prototxtFile = caffeInput['prototxt_file']
    self.ci_numFramesPerLeveldb = caffeInput['num_frames_per_leveldb']
    self.ci_allClassIds = caffeInput['all_classes']
    self.ci_backgroundClassIds = caffeInput['background_classes']

    # Post processing
    postProcessing = config['post_processing']
    self.pp_detectorThreshold = postProcessing['detector_threshold']

    # Curation
    curation = config['curation']
    self.cr_curationNumOfSets = curation['num_of_sets']
    self.cr_curationNumOfPatchPerSet = curation['num_of_patch_per_set']

    # PeaksExtractor config - not exposed to config.yaml
    # Connectedness of labeled example - have a full matrix structure
    self.pe_binaryStructure = ndimage.morphology.generate_binary_structure(2,2)
    # if the intersection between candidate labeled bbox and proposed subsume bbox
    # is more than 70%, then subsume the candidate labeled bbox
    self.pe_maxCandidateIntersectionDiff = 0.7
    # allow no more than 90% of intersection between subsumed boxes
    self.pe_maxSubsumedIntersectionDiff = 0.9
    # thresholds to subsample candidate labeled bbox prior to showing to user
    self.pe_curationPatchThresholds = [0.98, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

  @staticmethod
  def mkdir_p(path):
    """Util to make path"""
    try:
      os.makedirs(path)
    except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(path):
        pass
