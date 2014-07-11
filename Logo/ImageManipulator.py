import cv2
import numpy as np
import matplotlib.pyplot as plt

class ImageManipulator( object ):
  def __init__(self, imageFileName):
    self.imageFileName = imageFileName
    figure = plt.figure()
    self.axis = figure.add_subplot(111)

  def addPixelMap(self, pixelMap):
    """Overlay pixelMap as heatmap on top of image"""
    img = plt.imread(self.imageFileName)
    plt.imshow(img)
    plt.imshow(pixelMap, alpha = 0.5, vmin = 0.0, vmax = 1.0)
    plt.colorbar(orientation='horizontal')

  def addLabeledBbox(self, bbox, label):
    """Overlay bboxes with labels"""
    self.axis.add_patch(bbox.matplotlib_format())
    plt.text(bbox.x0 + 5, bbox.y0 + 25, label, fontsize=10)      

  def show(self):
    """Show whatever is in plt buffer"""
    plt.show()

  def extract_patch(self, bbox, outputPatchName, patchWidth, patchHeight, includeHeatmap = False):
    """Extract patch from image at specified bbox location"""
    img = cv2.imread(self.imageFileName)
    tX0 = int(bbox['x'])
    tY0 = int(bbox['y'])
    tW = int(bbox['x']) + int(bbox['width'])
    tH = int(bbox['y']) + int(bbox['height'])
    patch = img[tY0:tH, tX0:tW].copy()
    patch = cv2.resize(patch, (patchWidth, patchHeight))
    cv2.imwrite(outputPatchName, patch)

  def saveImage(self, outputFileName):
    """Save whatever is in plt buffer"""
    plt.savefig(outputFileName, bbox_inches='tight')
    plt.close('all')

