import os

from config.Config import Config

class VideoDataPath( object ):
  def __init__( self, baseDir, videoId, chiaVersionId ):
    self.base_path = os.path.join( baseDir, "%d" % videoId )
    Config.mkdir_p( self.base_path )

    self.scores_folder_path = os.path.join( self.base_path, "scores" ) 
    self.scores_path = os.path.join( self.scores_folder_path, "%d.hdf5" % chiaVersionId )
    Config.mkdir_p( self.scores_folder_path )

    self.quanta_folder_path = os.path.join( self.base_path, "quanta" )
    Config.mkdir_p( self.quanta_folder_path )

  def __str__( self ):
    return self.base_path
