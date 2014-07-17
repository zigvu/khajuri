import Queue, sys, os
import threading, time, pdb, glob

class RemovePatch( threading.Thread ):
  def __init__( self, queue ):
    super(RemovePatch, self).__init__()
    self.queue = queue

  def run( self ):
    while True:
      self.startNewJob()
      time.sleep( 0.1 )

  def startNewJob( self ):
    try:
      pngFile = self.queue.get( False )
      while pngFile:
      	pngFile = self.queue.get( False )
      	os.remove( pngFile )
    except Queue.Empty:
     pass

