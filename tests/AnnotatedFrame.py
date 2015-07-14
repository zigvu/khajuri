from config.Config import Config
import numpy as np
from postprocessing.type.Rect import Rect

class AnnotatedFrame( object ):
  def __init__( self ):
    self.annotations = []
    self.patchMapping = None
    self.frame = None

  def addAnnotation( self, annotation ):
    self.annotations.append( annotation )

class FrameDumpReader( object ):
  def __init__( self, fileName, maxAnnotationsPerFrame ):
    self.fileName = fileName
    self.frameNum = 0
    self.dump = {}
    self.maxAnnotationsPerFrame = maxAnnotationsPerFrame
    self.dump = np.load( open( self.fileName, 'r' ) )

  def __iter__( self ):
    return self

  def next( self ):
    if self.frameNum == len( self.dump ):
      raise StopIteration
    else:
      annotatedFrame = AnnotatedFrame( )
      for i in range( 0, self.maxAnnotationsPerFrame ):
        rect = self.dump[ self.frameNum, i * 4 : i* 4 + 4 ]
        if np.any( rect ):
          r = Rect( rect[ 0 ], rect[ 1 ], rect[ 2 ], rect[ 3 ] )
          annotatedFrame.addAnnotation( r )
      annotatedFrame.frame = self.dump[ self.frameNum, 4 * self.maxAnnotationsPerFrame: ]
      self.frameNum += 1 
      return annotatedFrame

class FrameDumpWriter( object ) :
    def __init__( self, numOfFrames,
            numOfPatchesPerFrame,
            maxAnnotationsPerFrame,
            fileName ):
      self.numOfFrames = numOfFrames
      self.numOfPatchesPerFrame = numOfPatchesPerFrame
      self.maxAnnotationsPerFrame  = maxAnnotationsPerFrame

      self.dump = np.zeros( ( numOfFrames, 4* maxAnnotationsPerFrame + numOfPatchesPerFrame  ),
        dtype=np.uint ) 

      self.frameNum = 0
      self.fileName = fileName

    def addFrame( self, annotatedFrame ):
      for i, rect in enumerate( annotatedFrame.annotations ):
        self.dump[ self.frameNum, i * 4 : i* 4 + 4 ] = np.asarray (
                      [ rect.x, rect.y, rect.w, rect.h ] )
      self.dump[ self.frameNum, 4*self.maxAnnotationsPerFrame : ] = annotatedFrame.frame.scores[0][ :, 0, 0 ]
      self.frameNum += 1
    
    def saveToFile( self ):
      np.save( open( self.fileName, 'w' ), self.dump )
