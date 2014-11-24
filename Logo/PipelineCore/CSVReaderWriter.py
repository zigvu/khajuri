import yaml, json, csv
from collections import OrderedDict

class CSVReaderWriter( object ):
  def __init__( self, fileName, create_new = False ):
    self.fileName = fileName
    self.myDict = OrderedDict()
    self.classIds = None
    if not create_new:
      patchFileName = None
      classIdMap = OrderedDict()
      with open(fileName, 'rb') as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
          for i, rowItem in enumerate(row):
            # get indices of class from header
            if idx == 0:
              if i == 0:
                pass
              else:
                classIdMap[i] = rowItem.split("_")[1]
            # once we have header, get individual class scores
            else:
              if i == 0:
                patchFileName = rowItem
                self.myDict[patchFileName] = OrderedDict()
              else:
                self.myDict[patchFileName][classIdMap[i]] = float(rowItem)
      # store classIds
      self.classIds = classIdMap.values()

  def getPatchFileNames( self ):
    return self.myDict.keys()

  def getClassIds( self ):
    return self.classIds

  def getScoreForPatchFileName( self, patchFileName ):
    return self.myDict[patchFileName]

  def getScoreForPatchFileNameClass( self, patchFileName, classId ):
    return self.myDict[patchFileName][classId]
