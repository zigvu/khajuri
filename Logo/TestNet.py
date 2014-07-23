import os, re
import caffe


class TestNet( object ):
  def __init__( self, prototxtFile, modelFile, classes ):
    self.prototxtFile = prototxtFile
    self.modelFile = modelFile
    self.classes = classes

  def run_net( self, leveldbFolder):
    # Create new prototxt file to point to right leveldb
    prototxtWithNewLeveldb = os.path.join(os.path.dirname(leveldbFolder), \
      'prototxt_%s' % os.path.basename(leveldbFolder))
    with open(self.prototxtFile) as fread:
      lines = fread.readlines()
    with open(prototxtWithNewLeveldb, "w") as fwrite:
      for line in lines:
        if "source:" in line:
          line = line.replace(re.findall(r'\"(.+?)\"', line)[0], leveldbFolder)
        fwrite.write("%s" % line)
    # Run testnet
    test_net = caffe.Net(prototxtWithNewLeveldb, self.modelFile)
    test_net.set_phase_test()
    test_net.set_mode_cpu()  ## TODO: Replace with configreader value
    output = test_net.forward()
    probablities = output['prob']
    numOfClasses = len( self.classes )
    scores = {}
    for i in range( 0, output[ 'label' ].size ):
      scores[ i ] = {}
      for j in range( 0, numOfClasses ):
        scores[ i ][ self.classes[ j ] ] = probablities.item( numOfClasses * i + j )
        print "Class: %d, score: %f" % (self.classes[ j ], scores[ i ][ self.classes[ j ] ])
    
  def prepareImageList( self, frameNum, patchList ):
    with open( "image_list.txt", "w" ) as f:
      for patchFileName in patchList:
        f.write( "%s 0\n" % patchFileName )
      f.write( "\n" )

  def computeScores( self, frameNum, patchList ):
    self.prepareImageList( frameNum, patchList )
    self.test_net = caffe.Net( self.prototxtFile, self.modelFile )
    self.test_net.set_phase_test()
    self.test_net.set_mode_gpu()
    output = self.test_net.forward()
    probablities = output['prob']
    numOfClasses = len( self.classes )
    scores = {}
    for i in range( 0, output[ 'label' ].size ):
      scores[ i ] = {}
      for j in range( 0, numOfClasses ):
        scores[ i ][ self.classes[ j ] ] = probablities.item( numOfClasses * i + j )
    return scores
