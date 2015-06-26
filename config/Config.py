import os, errno, shutil
import yaml, json
import logging

from multiprocessing import JoinableQueue

from Logo.PipelineMath.PixelMap import CellBoundaries
from Logo.PipelineMath.PixelMap import NeighborsCache

from config.ZLogging import ZLogging, ZLoggingQueueProducer

class Config:
  """Reads YAML config file and allows easy accessor to config attributes"""

  def __init__(self, configFileName):
    """Initlize config from YAML file"""
    config = yaml.load(open(configFileName, "r"))

    # Logging
    logs = config['logging']
    self.lg_log_level = logging.DEBUG
    if logs['log_level'] == 'INFO':
      self.lg_log_level = logging.INFO
    if logs['log_level'] == 'ERROR':
      self.lg_log_level = logging.ERROR
    if logs['log_level'] == 'CRITICAL':
      self.lg_log_level = logging.CRITICAL
    self.lg_cpp_log_started = False

    # TODO: get from kheer
    self.kheerJobId = 0
    self.environment = 'development'
    self.formatMsg = {
      'kheer_job_id': self.kheerJobId,
      'environment': self.environment
    }

    self.lg_rabbit_logger = logs['rabbit_logger'] == True
    self.lg_write_logs_to_queue = logs['write_logs_to_queue'] == True
    self.logQueue = JoinableQueue()
    if self.lg_rabbit_logger:
      self.lg_write_logs_to_queue = True
      # force only INFO and higher logs
      self.lg_log_level = logging.INFO

    self.cachedLogger = None

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
    self.sw_frame_width = int(slidingWindow['frame_width'])
    self.sw_frame_height = int(slidingWindow['frame_height'])
    self.sw_patchWidth = int(slidingWindow['output_width'])
    self.sw_patchHeight = int(slidingWindow['output_height'])

    self.sw_scales = []
    sw_temp_scales = slidingWindow['scaling']
    # Check length
    assert len(slidingWindow['x_stride']) == len(sw_temp_scales),\
        "Stride scale array and image arrays do not match"
    assert len(slidingWindow['y_stride']) == len(sw_temp_scales),\
        "Stride scale array and image arrays do not match"
    i = 0
    self.sw_xStride = {}
    self.sw_yStride = {}
    for sw_scale in sw_temp_scales:
      self.sw_scales = self.sw_scales + [float(sw_scale)]
      self.sw_xStride[float(sw_scale)] = slidingWindow['x_stride'][i]
      self.sw_yStride[float(sw_scale)] = slidingWindow['y_stride'][i]
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
    self.ci_ppQueue_maxSize = caffeInput['pp_queue_max_size']
    self.ci_ppQueue_highWatermark = caffeInput['pp_queue_high_watermark']
    self.ci_ppQueue_lowWatermark = caffeInput['pp_queue_low_watermark']
    self.ci_videoFrameNumberStart = caffeInput['video_frame_number_start']
    self.ci_useGPU = caffeInput['use_gpu'] == True
    self.ci_gpu_devices = caffeInput['gpu_devices']
    self.ci_saveVideoHeatmap = caffeInput['save_video_heatmap'] == True
    self.ci_computeFrameCuration = caffeInput['compute_frame_curation'] == True
    self.ci_runCaffePostProcessInParallel = caffeInput[
        'run_caffe_postprocess_in_parallel'
    ] == True
    self.ci_runCaffe = caffeInput['run_caffe'] == True
    self.ci_runPostProcess = caffeInput['run_postprocess'] == True
    self.ci_allClassIds = caffeInput['all_classes']
    self.ci_backgroundClassIds = caffeInput['background_classes']
    self.ci_nonBackgroundClassIds = [x for x in self.ci_allClassIds
                                     if x not in self.ci_backgroundClassIds]
    self.ci_heatMapClassIds = config['heatmap']['classes']
    self.ci_scoreTypes = {'prob': 0, 'fc8': 1}

    # Post processing
    postProcessing = config['post_processing']
    self.pp_detectorThreshold = postProcessing['detector_threshold']
    self.pp_savePatchScores = postProcessing['save_patch_scores'] == True
    self.pp_compressedJSON = postProcessing['compressed_json'] == True
    self.pp_zDistThresholds = postProcessing['z_dist_thresholds']
    ppResultWriters = postProcessing['result_writers']
    self.pp_resultWriterJSON = ppResultWriters['json_writer'] == True
    self.pp_resultWriterRabbit = ppResultWriters['rabbit_writer'] == True

    # Curation
    curation = config['curation']
    self.cr_curationNumOfSets = curation['num_of_sets']
    self.cr_curationNumOfItemsPerSet = curation['num_of_items_per_set']

    # HDF5 settings
    hdf5 = config['hdf5']
    self.hdf5_clip_frame_count = 1024
    self.hdf5_video_clips_map_filename = 'clips_map.json'
    self.hdf5_base_folder = hdf5['hdf5_base_folder']

    # Messaging settings
    messaging = config['messaging']
    self.mes_amqp_url = messaging['amqp_url']
    queueNames = messaging['queue_names']
    self.mes_q_vm2_kahjuri_development_video_data = queueNames[
        'vm2_kahjuri_development_video_data'
    ]
    self.mes_q_vm2_khajuri_development_log = queueNames[
        'vm2_khajuri_development_log'
    ]
    self.mes_q_vm2_kheer_development_clip_id_request = queueNames[
        'vm2_kheer_development_clip_id_request'
    ]
    self.mes_q_vm2_kheer_development_heatmap_rpc_request = queueNames[
        'vm2_kheer_development_heatmap_rpc_request'
    ]
    self.mes_q_vm2_kheer_development_localization_request = queueNames[
        'vm2_kheer_development_localization_request'
    ]

    # load memory heavy dictionaries on demand
    self.cachedCellBoundariesDict = None
    self.cachedNeighborMap = None

  @property
  def logger(self):
    if not self.cachedLogger:
      if self.lg_write_logs_to_queue:
        self.cachedLogger = ZLoggingQueueProducer(
          self.logQueue, self.lg_log_level, self.formatMsg).getLogger()
      else:
        self.cachedLogger = ZLogging(
          self.lg_log_level, self.formatMsg).getLogger()
    return self.cachedLogger

  @property
  def allCellBoundariesDict(self):
    if not self.cachedCellBoundariesDict:
      self.cachedCellBoundariesDict = CellBoundaries(self).allCellBoundariesDict
    return self.cachedCellBoundariesDict

  @property
  def neighborMap(self):
    if not self.cachedNeighborMap:
      neighborCache = NeighborsCache(self)
      self.cachedNeighborMap = neighborCache.neighborMapAllScales(
          self.allCellBoundariesDict)
    return self.cachedNeighborMap

  @staticmethod
  def mkdir_p(start_path):
    """Util to make path"""
    try:
      os.makedirs(start_path)
    except OSError as exc:  # Python >2.5
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
