#!/usr/bin/python
import glob, sys
import os, tempfile, pdb

# Add files to path
baseScriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append( '%s/Controller' % baseScriptDir )
sys.path.append( '%s/VideoReader'% baseScriptDir  )
for dir in glob.glob( '%s/plugins/*' % baseScriptDir  ):
	sys.path.append( dir )

import Config
from Frame import FrameGroup
from Plugin import PluginGroup, BlankDetection, BlurDetection
from Result import ResultGroup
from DetectionStrand import DetectionStrand, DetectionStrandGroup


class TempFileFS:    
    def __init__(self, videoFileName, config ):
        self.videoFileName = videoFileName
	self.config = config
        self.resultsFileName = os.path.join( os.path.dirname( self.videoFileName ), 
						"%s.json" % config.getCampaignId() )
    
    def system( self, cmd ):
        if os.system( cmd ):
	   raise Exception( 'Error with command: %s' % cmd )
	
    def __enter__(self):
	self.ramFSBaseDir = tempfile.mkdtemp()
	self.ramFSBaseFrameFolder = os.path.join( self.ramFSBaseDir, "frames" )
        self.regularFSBaseDir = os.path.dirname( self.videoFileName ) 
	self.regularFSBaseFrameFolder = os.path.join( self.regularFSBaseDir, "frames" )
        self.regularFSResultsFileName = os.path.join( self.regularFSBaseDir, "%s.json" % self.config.getCampaignId() )
        self.ramFSResultsFileName = os.path.join( self.ramFSBaseDir, "%s.json" % self.config.getCampaignId() )
	self.ramFSVideoFileName = os.path.join( self.ramFSBaseDir,  os.path.basename( self.videoFileName ) )
	self.system( "mount -t ramfs -o size=20m ramfs %s" % self.ramFSBaseDir )
	self.system( "cp %s %s" % ( self.videoFileName, self.ramFSVideoFileName ) )
	return self.ramFSVideoFileName

    def __exit__(self, *args):
        try:
           self.regularFSBaseDir = os.path.dirname( self.videoFileName ) 
	   self.regularFSBaseFrameFolder = os.path.join( self.regularFSBaseDir, "frames" )
           self.regularFSResultsFileName = os.path.join( self.regularFSBaseDir, "%s.json" % self.config.getCampaignId() )
           self.ramFSResultsFileName = os.path.join( self.ramFSBaseDir, "%s.json" % self.config.getCampaignId() )
	   self.ramFSVideoFileName = os.path.join( self.ramFSBaseDir,  os.path.basename( self.videoFileName ) )
	   self.system( "cp -r %s %s" % ( self.ramFSBaseFrameFolder, self.regularFSBaseDir ) )
	   self.system( "cp %s %s" % ( self.ramFSResultsFileName, self.regularFSResultsFileName ) )
	finally:
	   self.system( "umount -l %s" % self.ramFSBaseDir )

def processVideo( configPath, videoFilePath ):
	config = Config.Config( configPath )
	videoFileName = videoFilePath
        with TempFileFS( videoFilePath, config ) as tmpVideoFile:
		dsg = DetectionStrandGroup( tmpVideoFile, config )
		dsg.runVidPipe()

if __name__ == '__main__':
	if len( sys.argv ) < 3:
		print 'Usage %s <config.yaml> <video.file>' % sys.argv[ 0 ]
        else:
		processVideo( sys.argv[ 1 ], sys.argv[ 2 ] )
