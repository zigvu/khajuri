#!/usr/bin/env python
import boto, zipfile, os.path, os, tempfile, glob

class S3( object ):
  def __init__( self ):
    self.s3 = boto.connect_s3()
    self.videoResults = "chia-video-results"
  
  def saveJsonFolder( self, videoId, resultsFolder ):
     bucket = self.s3.get_bucket( self.videoResults )
     for f in glob.glob( os.path.join( resultsFolder, "*" ) ):
        key = bucket.new_key( '%s/jsonResult/%s' %  ( videoId, os.path.basename( f ) ) )
        key.set_contents_from_filename( f )
        key.set_acl('private')

  def saveJsonFile( self, videoId, jsonFile ):
     bucket = self.s3.get_bucket( self.videoResults )
     key = bucket.new_key( '%s/jsonResult/%s' %  ( videoId, os.path.basename( jsonFile ) ) )
     key.set_contents_from_filename( jsonFile )
     key.set_acl('private')
   
  def getJson( self, videoId ):
     bucket = self.s3.get_bucket( self.videoResults )
     s3JsonLocation = '%s/jsonResults/' % ( videoId )
     keys = bucket.list( s3JsonLocation )
     for k in keys:
        if k.name != s3JsonLocation:
           k.get_contents_to_filename( os.path.join( folderToSaveTo, k.name.split('/'[-1] ) ) )

  def saveVideoFolder( self, videoId, resultsFolder ):
     bucket = self.s3.get_bucket( self.videoResults )
     for f in glob.glob( os.path.join( resultsFolder, "*" ) ):
        key = bucket.new_key( '%s/video/%s' %  ( videoId, os.path.basename( f ) ) )
        key.set_contents_from_filename( f )
        key.set_acl('private')

  def saveVideoFile( self, videoId, videoFile ):
     bucket = self.s3.get_bucket( self.videoResults )
     key = bucket.new_key( '%s/video/%s' %  ( videoId, os.path.basename( videoFile ) ) )
     key.set_contents_from_filename( videoFile )
     key.set_acl('private')

if __name__ == "__main__":
  myconn = S3()
  import pdb; pdb.set_trace()
  
