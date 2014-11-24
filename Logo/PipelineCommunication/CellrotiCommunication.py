import sys, os, glob
import json, csv
from collections import OrderedDict
import logging
import pycurl, cStringIO, boto

class CellrotiCommunication( object ):
  """Class to connect to cellroti and get/put values"""
  def __init__(self):
    """Initialize values"""
    self.user_email = "X-User-Email:%s" % os.environ['CELLROTI_ZIGVU_ADMIN_EMAIL']
    self.user_auth = "X-User-Token:%s" % os.environ['CELLROTI_ZIGVU_ADMIN_AUTHORIZATION']

  def get_url(self, httpurl):
    """Performs an authenticated GET - returns parsed JSON"""
    c = pycurl.Curl()
    buf = cStringIO.StringIO()
    c.setopt(c.URL, httpurl)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.setopt(c.HTTPHEADER, [self.user_email, self.user_auth])
    c.perform()
    bufValue = buf.getvalue()
    buf.close()
    jsonDict = json.loads(bufValue)
    if (isinstance(jsonDict, dict)) and ("error" in jsonDict.keys()):
      raise RuntimeError("Couldn't authenticate with server")
    return jsonDict

  def post_url(self, httpurl, postData):
    """Performs an authenticated POST - returns parsed JSON"""
    postDataJSON = json.dumps(postData)
    c = pycurl.Curl()
    buf = cStringIO.StringIO()
    c.setopt(c.URL, httpurl)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.setopt(c.HTTPHEADER, [self.user_email, self.user_auth])
    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.POSTFIELDS, postDataJSON)
    c.perform()
    bufValue = buf.getvalue()
    buf.close()
    jsonDict = json.loads(bufValue)
    if (isinstance(jsonDict, dict)) and ("error" in jsonDict.keys()):
      raise RuntimeError("Couldn't authenticate with server")
    return jsonDict


  def s3_folder_write(self, s3Bucket, folder):
    """Write specified folder to S3 bucket"""
    pass

  def verify_s3_folder_write(self, s3Bucket, folder):
    """Verify write to S3 folder for each file"""
    pass
