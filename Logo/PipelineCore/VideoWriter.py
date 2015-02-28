import cv2
import cv2.cv as cv
import logging

class VideoWriter( object ):
  def __init__(self, videoFileName, fps, imageDim):
    """Initialize writer"""
    fourcc = cv.CV_FOURCC('M', 'J', 'P', 'G')
    self.writer = cv2.VideoWriter(videoFileName, fourcc, fps,\
      (imageDim.width, imageDim.height))
    self.frames = {}
    self.videoFileName = videoFileName
    self.lastFrameRead = 0

  def save(self):
    """Close write buffer and save the video"""
    logging.info( 'Saving %s Frames for video %s' % ( len( self.frames.items() ), self.videoFileName ) )
    if len( self.frames ) > 0:
      maxKeyNum = max( self.frames.keys() )
      while self.lastFrameRead <= maxKeyNum:
        k = self.lastFrameRead
        v = self.frames[ k ]
        logging.info( 'Saving Frame %s for video %s' % ( k, self.videoFileName ) )
        self.writer.write( v.getImage() )
        del self.frames[ k ]
        self.lastFrameRead += 1
 
  def close( self ):
    cv2.destroyAllWindows()
    self.writer.release()
