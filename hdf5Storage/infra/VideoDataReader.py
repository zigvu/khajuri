import h5py

from hdf5Storage.type.FrameData import FrameData
from hdf5Storage.type.VideoDataPath import VideoDataPath

class VideoDataReader( object ):
  def __init__( self, config, videoId, chiaVersionId ):
    self.config = config

    self.baseFolder = self.config.hdf5_base_folder
    self.frameDensity = self.config.sw_frame_density
    self.videoFrameNumberStart = self.config.ci_videoFrameNumberStart

    self.videoId = videoId
    self.chiaVersionId = chiaVersionId

    # create reader for hdf5 file
    self.videoDataPath = VideoDataPath( self.baseFolder, self.videoId, self.chiaVersionId )
    self.videoScoresFile = h5py.File( self.videoDataPath.scores_path, 'r' )
    self.createScoresDataSet()

  def createScoresDataSet( self ):
    '''
    The patch scores are stored in a 3-d numpy array
    1 dim => patches
    2 dim => classes
    3 dim => frame number
    '''
    self.scoresDataSet = self.videoScoresFile[ 'scores' ]
    if (( self.videoId != int( self.scoresDataSet.attrs[ 'video_id' ] )) or \
      ( self.chiaVersionId != int( self.scoresDataSet.attrs[ 'chia_version_id' ] ))):
      raise RuntimeError( 'VideoId or ChiaVersionId does not match' )

  def getFrameData( self, frameNumber ):
    fn = ( frameNumber - self.videoFrameNumberStart ) / self.frameDensity
    frameData = FrameData( self.videoId, self.chiaVersionId, fn )
    frameData.scores = self.scoresDataSet[ :, :, fn ]
    return frameData
 
  def close( self ):
    # close file
    self.videoScoresFile.close()

  # context manager helpers to enable usage of this class in `with` keyword
  def __enter__( self ):
    return self

  def __exit__( self, exception_type, exception_val, trace ):
    self.close()
