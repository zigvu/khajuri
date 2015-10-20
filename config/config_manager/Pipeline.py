import os
import json

from Logo.PipelineMath.BoundingBoxes import BoundingBoxes

class Pipeline(object):
  """Sets up pipeline related configs"""
  pass

class SlidingWindow(object):
  """Sets up sliding window related configs"""
  def __init__(self, configHash):
    """Initialize variables"""
    swHash = configHash['sliding_window']
    self.sw_frame_density = int(swHash['frame_density'])
    self.sw_frame_width = int(swHash['frame_width'])
    self.sw_frame_height = int(swHash['frame_height'])
    self.sw_patchWidth = int(swHash['patch_width'])
    self.sw_patchHeight = int(swHash['patch_height'])

    self.sw_scales = []
    sw_temp_scales = swHash['scaling']
    # Check length
    assert len(swHash['x_stride']) == len(sw_temp_scales),\
        "Stride scale array and image arrays do not match"
    assert len(swHash['y_stride']) == len(sw_temp_scales),\
        "Stride scale array and image arrays do not match"
    i = 0
    self.sw_xStride = {}
    self.sw_yStride = {}
    for sw_scale in sw_temp_scales:
      self.sw_scales = self.sw_scales + [float(sw_scale)]
      self.sw_xStride[float(sw_scale)] = swHash['x_stride'][i]
      self.sw_yStride[float(sw_scale)] = swHash['y_stride'][i]
      i += 1

    # score adjust factors
    self.sw_rescore_sigmoid_center = 0.5
    self.sw_rescore_sigmoid_steepness = 10

    self.staticBBoxes = BoundingBoxes(
        self.sw_frame_width, self.sw_frame_height, self.sw_xStride, 
        self.sw_yStride, self.sw_patchWidth, self.sw_patchHeight, self.sw_scales
    )
    # run through all scales once
    self.numOfSlidingWindows = self.staticBBoxes.getNumOfSlidingWindows()



class CaffeInput(object):
  """Sets up caffe input related configs"""
  def __init__(self, configHash):
    """Initialize variables"""
    caffeHash = configHash['caffe_input']
    self.ci_modelFile = caffeHash['model_file']
    self.ci_video_prototxtFile = caffeHash['video_prototxt_file']
    self.ci_savedBoundariesFile = caffeHash['saved_boundaries_file']
    self.ci_savedNeighborsFile = caffeHash['saved_neighbors_file']
    self.ci_lmdbBufferMaxSize = caffeHash['lmdb_buffer_max_size']
    self.ci_lmdbBufferMinSize = caffeHash['lmdb_buffer_min_size']
    self.ci_lmdbNumFramesPerBuffer = caffeHash['lmdb_num_frames_per_buffer']
    self.ci_ppQueue_maxSize = caffeHash['pp_queue_max_size']
    self.ci_ppQueue_highWatermark = caffeHash['pp_queue_high_watermark']
    self.ci_ppQueue_lowWatermark = caffeHash['pp_queue_low_watermark']
    self.ci_videoFrameNumberStart = caffeHash['video_frame_number_start']
    self.ci_runCaffe = caffeHash['run_caffe'] == True
    self.ci_runPostProcess = caffeHash['run_postprocess'] == True
    self.ci_allClassIds = caffeHash['all_classes']
    self.ci_backgroundClassIds = caffeHash['background_classes']
    self.ci_scoreTypes = {'prob': 0, 'fc8': 1}


class PostProcessing(object):
  """Sets up post processing related configs"""
  def __init__(self, configHash):
    """Initialize variables"""
    ppHash = configHash['post_processing']
    self.pp_detectorThreshold = ppHash['detector_threshold']
    self.pp_zDistThresholds = ppHash['z_dist_thresholds']
