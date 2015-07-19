import os
import errno
import shutil


class Utils(object):
  """Common utilities"""

  @staticmethod
  def mkdir_p(start_path):
    """Util to make path"""
    try:
      os.makedirs(start_path)
    except OSError as exc:  # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(start_path):
        pass

  @staticmethod
  def rm_rf(start_path):
    """Util to delete path"""
    try:
      if os.path.isdir(start_path):
        shutil.rmtree(start_path, ignore_errors=True)
      elif os.path.exists(start_path):
        os.remove(start_path)
    except:
      # do nothing
      pass

  @staticmethod
  def dir_size(start_path):
    """Util to get total size of path in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
      for f in filenames:
        fp = os.path.join(dirpath, f)
        if os.path.exists(fp):
          try:
            total_size += os.path.getsize(fp)
          except:
            continue
    # convert to MB
    return int(total_size * 1.0 / 10000000)
