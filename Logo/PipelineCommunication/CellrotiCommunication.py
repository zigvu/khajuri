import sys, os, glob
import json, csv
from collections import OrderedDict
import logging
import pycurl, cStringIO, boto, pysftp

class CellrotiCommunication( object ):
  """Class to connect to cellroti and get/put values"""
  def __init__(self):
    """Initialize values"""
    self.user_email = "X-User-Email:%s" % os.environ['CELLROTI_ZIGVU_ADMIN_EMAIL']
    self.user_auth = "X-User-Token:%s" % os.environ['CELLROTI_ZIGVU_ADMIN_AUTHORIZATION']
    self.private_key_location = os.environ['SSH_PRIVATE_KEY_LOCATION']

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

  def send_data_to_cellroti(self, folder, storageSelection, storageLocation):
    """Send data to cellroti server"""
    successStatus = False
    videoId = self.get_video_id(folder)

    # storage location strings should match in config.yaml
    if storageSelection == 'SOFTLAYER':
      storageLocation = "%s/%d" % (storageLocation, videoId)
      successStatus = self.save_folder_to_softlayer(folder, storageLocation)
    elif storageSelection == 'S3':
      # modify bucket with right path
      successStatus = self.save_folder_to_s3(folder, storageLocation)
    else:
      raise RuntimeError("Cellroti storage selection not recognized")

    saveState = {'video_id': videoId, 'success': successStatus}
    return saveState

  def save_folder_to_softlayer(self, folder, softlayerLocation):
    """Save specified folder to softlayer location"""
    successStatus = True

    username, ipaddress, uploadFolder = self.parse_softlayer_storage_location(softlayerLocation)
    sftp = pysftp.Connection(ipaddress, username=username, private_key=self.private_key_location)
    try:
      sftp.mkdir(uploadFolder)
    except:
      successStatus = False
      logging.error("Couldn't make folder %s in remote" % uploadFolder)
    try:
      sftp.put_r(folder, uploadFolder, confirm=True)
    except:
      successStatus = False
      logging.error("Couldn't upload data to remote")

    return successStatus

  def save_folder_to_s3(self, folder, s3Location):
    """Save specified folder to S3 bucket"""
    pass

  def get_video_id(self, folder):
    """Reads localization file and gets video id"""
    # BEGIN: these match with what is in PostProcessDataExtractor.py file
    outputJSONFileName = os.path.join(folder, "localizations.json")

    jsonToSave = json.load(open(outputJSONFileName, "r"))
    videoId = jsonToSave['video_id']
    # END: these match with what is in PostProcessDataExtractor.py file
    return videoId

  def parse_softlayer_storage_location(self, softlayerLocation):
    """Return username, IP and foldername for softlayer"""
    username = softlayerLocation.split("@")[0]
    ipaddress = softlayerLocation.split("@")[1].split("/")[0]
    uploadFolder = softlayerLocation.split(ipaddress)[1]
    return username, ipaddress, uploadFolder
