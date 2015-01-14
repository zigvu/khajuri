import glob, os
import multiprocessing
from multiprocessing import JoinableQueue, Queue, Process, Manager
from operator import itemgetter
import logging, json

from Logo.PipelineMath.Rectangle import Rectangle

from Logo.PipelineCore.ConfigReader import ConfigReader
from Logo.PipelineCore.CurationManager import CurationManager
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoFrameReader import VideoFrameReader

def runSingleDumper(sharedDict, curationDataQueue):
  """Process to extract curation/localizations from single JSON file"""
  outputFolder = sharedDict['outputFolder']
  videoFileName = sharedDict['videoFileName']
  patchWidth = sharedDict['patch_width']
  patchHeight = sharedDict['patch_height']

  videoFrameReader = VideoFrameReader(videoFileName)
  frame = videoFrameReader.getFrameWithFrameNumber(int(1))
  while frame != None:
    curationData = curationDataQueue.get()
    if curationData is None:
      curationDataQueue.task_done()
      # Poison pill means done with json reading
      break
    # read data
    frameNumber = curationData['frame_number']
    frame = videoFrameReader.getFrameWithFrameNumber(int(frameNumber))
    if frame != None:
      logging.debug("Working on frame number %d" % frameNumber)

      frameFileName = os.path.join(outputFolder, "frame_%s.png" % frameNumber)
      videoFrameReader.savePngWithFrameNumber(int(frameNumber), str(frameFileName))
      imageManipulator = ImageManipulator(frameFileName)

      for curationPatch in curationData['curation_patches']:
        bbox = Rectangle.rectangle_from_json(curationPatch['bbox'])
        patchFolderName = os.path.join(outputFolder, curationPatch['patch_foldername'])
        ConfigReader.mkdir_p(patchFolderName)
        patchFileName = os.path.join(patchFolderName, curationPatch['patch_filename'])
        imageManipulator.extract_patch(bbox, patchFileName, patchWidth, patchHeight)
      # delete image file
      ConfigReader.rm_rf(frameFileName)
    # note as task done
    curationDataQueue.task_done()

  # done with dumping - close video reader
  videoFrameReader.close()

class CurationPatchDumper(object):
  def __init__(self, configReader, videoFileName, jsonFolder, outputFolder):
    """Initialize values"""
    self.configReader = configReader
    self.videoFileName = videoFileName
    self.jsonFolder = jsonFolder
    self.outputFolder = outputFolder
    ConfigReader.mkdir_p(outputFolder)

    #self.num_consumers = max(int(self.configReader.multipleOfCPUCount * multiprocessing.cpu_count()), 1)
    self.num_consumers = 1

  def run():
    """Start patch dumpers"""
    logging.debug("Dumper main thread: Setting up %d dump threads" % self.num_consumers)

    # set up queues
    curationDataQueue = JoinableQueue(maxsize = self.num_consumers * 2)
    sharedManager = Manager()
    sharedDict = sharedManager.dict()
    sharedDict['outputFolder'] = self.outputFolder
    sharedDict['videoFileName'] = self.videoFileName
    sharedDict['patch_width'] = self.configReader.sw_patchWidth
    sharedDict['patch_height'] = self.configReader.sw_patchHeight

    # start multiple dumpers
    singlePatchDumpers = []
    for i in xrange(self.num_consumers):
      singlePatchDumper = Process(\
        target=runSingleDumper,\
        args=(sharedDict, curationDataQueue))
      singlePatchDumpers += [singlePatchDumper]
      singlePatchDumper.start()

    # feed curation queue
    curationManager = CurationManager(self.jsonFolder, self.configReader)
    for frameNumber in curationManager.getFrameNumbers():
      curationData = {}
      curationData['frame_number'] = frameNumber
      curationData['curation_patches'] = curationManager.getCurationPatches(frameNumber)
      curationDataQueue.put(curationData)

    # all curations are in queue - wait for completion
    for i in xrange(self.num_consumers):
      # for each process, put a poison pill in queue
      curationDataQueue.put(None)

    curationDataQueue.join()

    logging.debug("Dumper main thread: Waiting for threads to join")
    for singlePatchDumper in singlePatchDumpers:
      singlePatchDumper.join()

    logging.debug("Dumper main thread: Done with all extractions")
