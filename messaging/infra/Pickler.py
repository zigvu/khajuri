import cPickle, cStringIO

class Pickler( object ):
  @staticmethod
  def pickle( obj ):
    """Util to pickle this object"""
    iostr = cStringIO.StringIO()
    cPickle.dump( obj, iostr )
    iostr.seek( 0 )
    pckldValue = iostr.getvalue()
    iostr.close()
    return pckldValue

  @staticmethod
  def unpickle( obj ):
    return cPickle.load( cStringIO.StringIO( obj ) )
