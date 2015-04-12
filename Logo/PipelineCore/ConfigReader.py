import os, errno, shutil
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
    # for recurring logs, set interval to print
    self.logIntervalSeconds = 5

    # CPU count
    self.multipleOfCPUCount = float(config['multiple_of_cpu_count'])

    # Sliding window creation:
    slidingWindow = config['sliding_window']
    sw_folders = slidingWindow['folders']
    self.sw_folders_frame = sw_folders['frame_output']
    self.sw_folders_patch = sw_folders['patch_output']
    self.sw_folders_json = sw_folders['json_output']
    self.sw_folders_leveldb = sw_folders['levedb_output']
    self.sw_folders_video = sw_folders['video_output']
    self.sw_folders_numpy = sw_folders['numpy_output']

    self.sw_frame_density = int(slidingWindow['frame_density'])
    self.sw_patchWidth = int(slidingWindow['output_width'])
    self.sw_patchHeight = int(slidingWindow['output_height'])

    self.sw_scales = []
    sw_temp_scales = slidingWindow['scaling']
    # Check length
    assert len( slidingWindow['x_stride'] ) == len( sw_temp_scales ),\
        "Stride scale array and image arrays do not match"
    assert len( slidingWindow['y_stride'] ) == len( sw_temp_scales ),\
        "Stride scale array and image arrays do not match"
    i = 0 
    self.sw_xStride = {}
    self.sw_yStride = {}
    for sw_scale in sw_temp_scales:
      self.sw_scales = self.sw_scales + [float(sw_scale)]
      self.sw_xStride[ float(sw_scale) ] = slidingWindow['x_stride'][ i ] 
      self.sw_yStride[ float(sw_scale) ] = slidingWindow['y_stride'][ i ] 
      i += 1

    # Scale decay factors
    decayFactorFileName = os.path.join(os.path.dirname(configFileName),\
        slidingWindow['scale_decayed_factors_file'])
    sdf = json.load(open(decayFactorFileName, 'r'))
    self.sw_scale_decay_factors = sdf['scaleDecayFactors']
    self.sw_scale_decay_sigmoid_center = 0.5
    self.sw_scale_decay_sigmoid_steepness = 10
    # check that JSON decay has all scale combinations
    sdfScales = []
    for sd in self.sw_scale_decay_factors:
        sdfScales += [sd['scale']]
        sdScales = []
        for sdFactor in sd['factors']:
            sdScales += [sdFactor['scale']]
        assert sdScales == self.sw_scales, "JSON scale decay does NOT match with config scales"
    assert sdfScales == self.sw_scales, "JSON scale decay does NOT match with config scales"


    # Caffe input
    caffeInput = config['caffe_input']
    self.ci_modelFile = caffeInput['model_file']
    self.ci_video_prototxtFile = caffeInput['video_prototxt_file']
    self.ci_deploy_prototxtFile = caffeInput['deploy_prototxt_file']
    self.ci_numFramesPerLeveldb = caffeInput['num_frames_per_leveldb']
    self.ci_numConcurrentLeveldbs = caffeInput['num_concurrent_leveldbs']
    self.ci_maxLeveldbSizeMB = caffeInput['max_leveldb_size_mb']
    self.ci_lmdbBufferMaxSize = caffeInput['lmdb_buffer_max_size']
    self.ci_lmdbBufferMinSize = caffeInput['lmdb_buffer_min_size']
    self.ci_lmdbNumFramesPerBuffer = caffeInput['lmdb_num_frames_per_buffer']
    self.ci_videoFrameNumberStart = caffeInput['video_frame_number_start']
    self.ci_useGPU = caffeInput['use_gpu'] == True
    self.ci_gpu_devices = caffeInput['gpu_devices']
    self.ci_saveVideoHeatmap = caffeInput['save_video_heatmap'] == True
    self.ci_computeFrameCuration = caffeInput['compute_frame_curation'] == True
    self.ci_runCaffePostProcessInParallel = caffeInput['run_caffe_postprocess_in_parallel'] == True
    self.ci_runCaffe = caffeInput['run_caffe'] == True
    self.ci_runPostProcess = caffeInput['run_postprocess'] == True
    self.ci_allClassIds = caffeInput['all_classes']
    self.ci_backgroundClassIds = caffeInput['background_classes']
    self.ci_nonBackgroundClassIds = [x for x in self.ci_allClassIds if x not in self.ci_backgroundClassIds]
    self.ci_heatMapClassIds = config[ 'heatmap' ] [ 'classes' ]

    # Post processing
    postProcessing = config['post_processing']
    self.pp_detectorThreshold = postProcessing['detector_threshold']
    self.pp_savePatchScores = postProcessing['save_patch_scores'] == True
    self.pp_compressedJSON = postProcessing['compressed_json'] == True

    # Curation
    curation = config['curation']
    self.cr_curationNumOfSets = curation['num_of_sets']
    self.cr_curationNumOfItemsPerSet = curation['num_of_items_per_set']

    # Cellroti
    cellroti = config['cellroti']
    ce_urls = cellroti['urls']
    self.ce_urls_getDetectables = ce_urls['get_detectables']
    self.ce_urls_postResults = ce_urls['post_results']

    self.ce_storageSelection = cellroti['storage_selection']
    self.ce_storageLocation = cellroti['storage_location']
    self.ce_numSecondsPerSampleFrame = cellroti['num_seconds_per_sample_frame']



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
  def mkdir_p(start_path):
    """Util to make path"""
    try:
      os.makedirs(start_path)
    except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(start_path):
        pass

  @staticmethod
  def rm_rf(start_path):
    """Util to delete path"""
    try:
      if os.path.isdir(start_path):
        shutil.rmtree(start_path, ignore_errors=True)
      elif os.path.exists(start_path):
        os.remove(start_path)
    except:
      # do nothing
      pass

  @staticmethod
  def dir_size(start_path):
    """Util to get total size of path in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
      for f in filenames:
        fp = os.path.join(dirpath, f)
        if os.path.exists(fp):
          try:
            total_size += os.path.getsize(fp)
          except:
            continue
    # convert to MB
    return int(total_size * 1.0 / 10000000)
