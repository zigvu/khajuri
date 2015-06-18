import numpy as np
from shapely.geometry import Polygon
from matplotlib.path import Path
import matplotlib.patches as patches


class Rectangle(Polygon):
  """General purpose rectangle"""

  def __init__(self, polyArray):
    """Initialize class"""
    Polygon.__init__(self, polyArray)
    self.width = int(self.bounds[2] - self.bounds[0])
    self.height = int(self.bounds[3] - self.bounds[1])
    polyCenter = self.centroid
    self.centerX = int(polyCenter.x)
    self.centerY = int(polyCenter.y)
    self.x0 = self.bounds[0]
    self.y0 = self.bounds[1]

  def get_scaled_rectangle(self, scaleFactor):
    """Get a new rectangle scaled according to given scale factor
    Returns new rectangle
    """
    b = np.asarray(self.exterior)
    scaledRect = Rectangle([
        (b[0][0], b[0][1]), (b[1][0] * scaleFactor, b[1][1]),
        (b[2][0] * scaleFactor, b[2][1] * scaleFactor),
        (b[3][0], b[2][1] * scaleFactor)
    ])
    return scaledRect

  def numpy_format(self):
    """Convert shapely polygon to numpy array"""
    ext = np.asarray(self.exterior)
    return np.array(ext[0:4, :], np.float32)

  def cv2_format(self):
    """Convert shapely polygon to cv2 polygon points"""
    ext = np.asarray(self.exterior)
    b = np.array(ext[0:4, :], np.int32)
    return b.reshape((-1, 1, 2))

  def matplotlib_format(self):
    """Convert shapely polygon to matplotlib patch"""
    b = np.asarray(self.exterior)
    verts = [
        (b[3][0], b[3][1]), (b[0][0], b[0][1]), (b[1][0], b[1][1]),
        (b[2][0], b[2][1]), (b[3][0], b[3][1])
    ]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    path = Path(verts, codes)
    patch = patches.PathPatch(path, edgecolor='red', lw=1, fill=False)
    return patch

  def json_format(self):
    """Convert shapely polygon to json format"""
    return {
        'x': self.x0,
        'y': self.y0,
        'width': self.width,
        'height': self.height
    }

  @staticmethod
  def rectangle_from_endpoints(x0, y0, x2, y2):
    """Get rectangle based on end points"""
    rect = Rectangle([(x0, y0), (x2, y0), (x2, y2), (x0, y2)])
    return rect

  @staticmethod
  def rectangle_from_dimensions(width, height):
    """Get rectangle based on dimension starting at 0,0"""
    rect = Rectangle([(0, 0), (width, 0), (width, height), (0, height)])
    return rect

  @staticmethod
  def rectangle_from_json(bbox):
    """Get rectangle based on bbox json"""
    rect = Rectangle([
        (int(bbox['x']), int(bbox['y'])),
        (int(bbox['x']) + int(bbox['width']), int(bbox['y'])), (
            int(bbox['x']) + int(bbox['width']),
            int(bbox['y']) + int(bbox['height'])
        ), (int(bbox['x']), int(bbox['y']) + int(bbox['height']))
    ])
    return rect

  @staticmethod
  def rectangle_from_centers(centerX, centerY, width, height, largerRect=None):
    """Get rectangle based on dimension centered on X,Y
    Optionally, specify largerRect if returned rectangle needs to be within
    """
    x0 = x3 = int(centerX - width / 2)
    x1 = x2 = int(centerX + width / 2)
    y0 = y1 = int(centerY - height / 2)
    y2 = y3 = int(centerY + height / 2)

    if x0 < 0:
      x1 = x2 = int(centerX + width / 2) + abs(x0)
      x0 = x3 = 0
    if y0 < 0:
      y2 = y3 = int(centerY + height / 2) + abs(y0)
      y0 = y1 = 0

    if largerRect != None:
      if x1 > largerRect.width:
        x1 = x2 = largerRect.width
      if y2 > largerRect.height:
        y2 = y3 = largerRect.height

    # if desired output is square, return back square
    if width == height:
      minWH = min((x1 - x0), (y2 - y0))
      x1 = x2 = x0 + minWH
      y2 = y3 = y0 + minWH

    rect = Rectangle([(x0, y0), (x1, y1), (x2, y2), (x3, y3)])
    return rect

  def __str__(self):
    b = self.bounds
    return "X: " + str(int(b[0])) + \
      ", Y: " + str(int(b[1])) + \
      ", W: " + str(int(b[2] - b[0])) + \
      ", H: " + str(int(b[3] - b[1]))
