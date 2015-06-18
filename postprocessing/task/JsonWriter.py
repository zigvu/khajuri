import logging, json
import os

from postprocessing.task.Task import Task


class JsonWriter(Task):

  def __call__(self, obj):
    frame, classIds = obj
    logging.info(
        'JsonWriter: Saving frameInfo on %s for classes %s' % (frame, classIds))
    localizations = {}
    scores = {}
    myDict = {}
    myDict["frame_number"] = frame.frameNumber
    myDict["frame_time"] = frame.frameDisplayTime
    for classId in self.config.ci_allClassIds:
      scores[classId] = {}
      scores[classId]["fc8"] = list(frame.scores[0][:, classId, 1])
      scores[classId]["prob"] = list(frame.scores[0][:, classId, 0])

      #scores[ classId ] [ "fc8" ] = map( float,
      #    map( "{0:.3f}".format,
      #      ( frame.scores[0][ :, classId, 1 ] ) ) )
      #scores[ classId ] [ "prob" ] = map( float,
      #    map( "{0:.3f}".format,
      #      ( frame.scores[0][ :, classId, 0 ] ) ) )
      if frame.localizations.get(int(classId)):
        localizations[classId] = []
        for loc in frame.localizations[int(classId)]:
          bbox = {}
          bbox["scale"] = loc.scale
          bbox["score"] = loc.score
          bbox["zdist_thresh"] = loc.zDistThreshold
          bbox["bbox"] = {
              "height": loc.rect.h,
              "width": loc.rect.w,
              "x": loc.rect.x,
              "y": loc.rect.y
          }
          localizations[classId].append(bbox)

    myDict["scores"] = scores
    myDict["localizations"] = localizations
    if not frame.filename:
      frame.filename = os.path.join(
          self.config.json_output_folder,
          "%s_frame_%s.json" % (self.config.videoId, frame.frameNumber))
    json.dump(myDict, open(frame.filename, 'w'), indent=2)
    return (frame, classIds)
