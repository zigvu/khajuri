from postprocessing.task.Task import Task

from postprocessing.task.CompareFrame import CompareFrame
from postprocessing.task.OldJsonReader import OldJsonReader
from postprocessing.task.JsonReader import JsonReader


class CompareFiles(Task):
  reader = {'old': OldJsonReader, 'new': JsonReader,}

  def __call__(self, obj):
    self.logger.debug('Got %s, %s, %s, %s for comparison' % obj)
    j, jFormat, k, kFormat = obj
    # Take an item out from the Queue, read it, compare it, put the results into the queue
    # Compile the Result
    frame1, classIds = self.reader[jFormat](self.config, self.status)(j)
    frame2, classIds = self.reader[kFormat](self.config, self.status)(k)
    result = CompareFrame(self.config, self.status)((frame1, frame2))
    return result
