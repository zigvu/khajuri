import os, glob, time, json
import multiprocessing
from multiprocessing import JoinableQueue, Process, Manager
import logging

from Logo.PipelineCore.VideoFrameReader import VideoFrameReader
from Logo.PipelineCore.ImageManipulator import ImageManipulator
from Logo.PipelineCore.VideoWriter import VideoWriter
from Logo.PipelineCore.ConfigReader import ConfigReader

def runAviToMp4Converter( conversionQueue ):
  """Process to convert avi to mp4 file"""
  while True:
    quantaFileName = conversionQueue.get()
    if quantaFileName is None:
      conversionQueue.task_done()
      # poison pill means done with video conversion
      break
    logging.debug("Start video conversion of file %s" % os.path.basename(quantaFileName))
    # Set up output video
    aviFolder = os.path.dirname(quantaFileName)
    aviFile = os.path.basename(quantaFileName).split('.')[0]
    mp4FileName = os.path.join(aviFolder, "%s.mp4" % (aviFile))
    # exec call
    os.system("ffmpeg -i %s %s" % (quantaFileName, mp4FileName))
    os.remove(quantaFileName)
    conversionQueue.task_done()
    logging.debug("Done video conversion of file %s" % os.path.basename(quantaFileName))


class VideoSplitterThread( object ):
  """Class to draw split video into quanta"""
  def __init__(self, configFileName, videoFileName, quantaOutputFolder):
    """Initialize values"""
    self.configReader = ConfigReader(configFileName)
    self.videoFileName = videoFileName
    self.quantaOutputFolder = quantaOutputFolder
    self.tempFolder = '/mnt/tmp'

    # TODO: get from config/kheer
    self.numFrameInQuanta = 1024    
    self.videoQuantaMapFilename = os.path.join( self.quantaOutputFolder, 'quanta_map.json' )
    # self.numFrameInQuanta = self.configReader.hdf5_quanta_frame_count
    # self.videoQuantaMapFilename = os.path.join( self.quantaOutputFolder, self.configReader.video_quanta_map_filename )
    self.frameDensity = self.configReader.sw_frame_density

    ConfigReader.mkdir_p(self.quantaOutputFolder)

    # Logging levels
    logging.basicConfig(format='{%(filename)s::%(lineno)d::%(asctime)s} %(levelname)s - %(message)s', 
      level=self.configReader.log_level, datefmt="%Y-%m-%d--%H:%M:%S")

  def run( self ):
    """Split video based on quanta"""
    startTime = time.time()
    logging.info("Setting up video split for video %s" % self.videoFileName)

    # keep track of frame numbers for each quanta
    videoQuantaMap = {}

    # conversion threads
    conversionQueue = JoinableQueue()
    conversionProcesses = []
    # num_consumers = 1
    num_consumers = max(int(self.configReader.multipleOfCPUCount * multiprocessing.cpu_count()), 1)
    for i in xrange(num_consumers):
      conversionProcess = Process(\
        target=runAviToMp4Converter,\
        args=(conversionQueue,))
      conversionProcesses += [conversionProcess]
      conversionProcess.start()

    videoFrameReader = VideoFrameReader(self.videoFileName)
    fps = videoFrameReader.getFPS()
    imageDim = videoFrameReader.getImageDim()

    # quanta number
    quantaId = 0
    videoWriter = None
    outVideoFileName = None
    currentFrameNum = 0 # frame number being extracted

    frame = videoFrameReader.getFrameWithFrameNumber(int(self.configReader.ci_videoFrameNumberStart))
    while frame != None:
      if ((currentFrameNum % self.numFrameInQuanta) == 0):
        if videoWriter != None:
          # close video and kick off mp4 conversion
          videoWriter.save()
          conversionQueue.put(outVideoFileName)
          videoQuantaMap[quantaId]['frame_number_end'] = ( currentFrameNum - 1 )
          quantaId += 1
        logging.debug("Creating new video id: %d" % quantaId)
        outVideoFileName = os.path.join(self.quantaOutputFolder, "%d.avi" % quantaId)
        videoWriter = VideoWriter(outVideoFileName, fps, imageDim)
        videoQuantaMap[quantaId] = {\
          'quanta_filename': "%d.mp4" % quantaId,\
          'frame_number_start': currentFrameNum\
        }

      logging.debug("Adding frame %d to video" % currentFrameNum)
      # Save each frame
      imageFileName = os.path.join(self.tempFolder, "temp_%d.png" % currentFrameNum)
      videoFrameReader.savePngWithFrameNumber(int(currentFrameNum), str(imageFileName))
      imgManipulator = ImageManipulator(imageFileName)
      # Add to video and remove temp file
      videoWriter.addFrame(imgManipulator)
      os.remove(imageFileName)
      # increment frame number
      currentFrameNum += 1
      frame = videoFrameReader.getFrameWithFrameNumber(int(currentFrameNum))

    # close last video writer
    if videoWriter != None:
      # close video and kick off mp4 conversion
      videoWriter.save()
      conversionQueue.put(outVideoFileName)
      videoQuantaMap[quantaId]['frame_number_end'] = ( currentFrameNum - 1 )

    # write map file
    with open( self.videoQuantaMapFilename, "w" ) as f :
      json.dump( videoQuantaMap, f, indent=2 )

    # Close video reader
    videoFrameReader.close()

    # join conversion threads
    logging.info("Waiting for mp4 conversion threads to complete")
    for i in xrange(num_consumers):
      conversionQueue.put(None)
    conversionQueue.join()
    logging.debug("Mp4 conversion queues joined")
    for conversionProcess in conversionProcesses:
      conversionProcess.join()
    logging.debug("Mp4 conversion processes joined")      

    # Exit
    logging.info("Finished creating videos")
    endTime = time.time()
    logging.info( 'It took VideoSplitterThread %s seconds to complete' % ( endTime - startTime ) )
