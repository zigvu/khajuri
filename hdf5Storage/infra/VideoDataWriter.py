import h5py

from hdf5Storage.type.VideoDataPath import VideoDataPath

class VideoDataWriter( object ):
  def __init__( self, config, videoId, chiaVersionId ):
    self.config = config

    self.baseFolder = self.config.hdf5_base_folder
    self.numFrameInQuanta = self.config.hdf5_quanta_frame_count
    self.numClassIds = len( self.config.ci_allClassIds )
    self.numTotalPatches = self.config.total_num_of_patches
    self.frameDensity = self.config.sw_frame_density
    self.videoFrameNumberStart = self.config.ci_videoFrameNumberStart

    self.videoId = videoId
    self.chiaVersionId = chiaVersionId

    self.curFrameDataCounter = 0

    # create new file in hdf5
    self.videoDataPath = VideoDataPath( self.baseFolder, self.videoId, self.chiaVersionId )
    self.videoScoresFile = h5py.File( self.videoDataPath.scores_path, 'w' )
    self.createScoresDataSet()
    # self.localizationDset = self.createLocalizationDataSet()

  def createScoresDataSet( self ):
    '''
    The patch scores are stored in a 3-d numpy array
    1 dim => patches
    2 dim => classes
    3 dim => frame number
    '''
    self.scoresDataSet = self.videoScoresFile.create_dataset(
      'scores',
      ( self.numTotalPatches, self.numClassIds, self.numFrameInQuanta ),
      maxshape=( self.numTotalPatches, self.numClassIds, None ),
      dtype='float16',
      chunks=( self.numTotalPatches, self.numClassIds, 1 ),
      compression='gzip',
      compression_opts=9 
    )
    self.scoresDataSet.attrs[ 'video_id' ] = self.videoId
    self.scoresDataSet.attrs[ 'chia_version_id' ] = self.chiaVersionId

  def addFrameData( self, frameData ):
    frameNumber = ( frameData.frameNumber - self.videoFrameNumberStart ) / self.frameDensity
 
    # if we are at the size limit of dataset, resize
    if frameNumber >= self.scoresDataSet.shape[ 2 ]:
      # resize to the nearest quanta boundary
      newSizeNum = frameNumber - ( frameNumber % self.numFrameInQuanta ) + self.numFrameInQuanta
      self.scoresDataSet.resize( (
        self.numTotalPatches,
        self.numClassIds,
        newSizeNum
      ) )
    # add data
    self.scoresDataSet[ :, :, frameNumber ] = frameData.scores
    self.curFrameDataCounter += 1

  def close( self ):
    # trim, flush and close
    self.scoresDataSet.resize( (
      self.numTotalPatches,
      self.numClassIds,
      ( self.curFrameDataCounter - 1 )
    ) )
    self.videoScoresFile.flush()
    self.videoScoresFile.close()

  # context manager helpers to enable usage of this class in `with` keyword
  def __enter__( self ):
    return self

  def __exit__( self, exception_type, exception_val, trace ):
    self.close()
