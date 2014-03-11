#!/usr/bin/python
import glob, sys
import os, tempfile, pdb

class TempFileFS:    
    def __init__(self, videoFileName ):
        self.videoFileName = videoFileName
        self.regularFSBaseDir= os.path.dirname( self.videoFileName ) 
    
    def system( self, cmd ):
        if os.system( cmd ):
	   raise Exception( 'Error with command: %s' % cmd )
	
    def __enter__(self):
	self.ramFSBaseDir = tempfile.mkdtemp( dir="/mnt/tmp" )
	return self.ramFSBaseDir

    def __exit__(self, *args):
        try:
	   self.system( "cp -r %s/* %s" % ( self.ramFSBaseDir, self.regularFSBaseDir ) )
	finally:
	   self.system( "rm -rf %s" % self.ramFSBaseDir )
