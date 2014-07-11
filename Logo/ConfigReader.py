import yaml, json
import scipy.ndimage as ndimage

class ConfigReader:
  """Reads YAML config file and allows easy accessor to config attributes"""
  def __init__(self, configFileName):
    """Initlize config from YAML file"""
    config = yaml.load(open(configFileName, "r"))

    # Sliding window creation:
    slidingWindow = config['sliding_window']
    self.sw_patchWidth = int(slidingWindow['output_width'])
    self.sw_patchHeight = int(slidingWindow['output_height'])
    self.sw_xStride = int(slidingWindow['x_stride'])
    self.sw_yStride = int(slidingWindow['y_stride'])

    # Post processing
    postProcessing = config['post_processing']
    self.pp_backgroundClassIds = postProcessing['background_classes']
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

