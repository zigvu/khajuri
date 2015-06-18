import cPickle, cStringIO


class Pickler(object):
  """Fast pickling/unpickling of objects"""

  @staticmethod
  def pickle(obj):
    """Util to pickle this object"""
    iostr = cStringIO.StringIO()
    cPickle.dump(obj, iostr)
    iostr.seek(0)
    pckldValue = iostr.getvalue()
    iostr.close()
    return pckldValue

  @staticmethod
  def unpickle(obj):
    """Util to unpickle this object"""
    return cPickle.load(cStringIO.StringIO(obj))
