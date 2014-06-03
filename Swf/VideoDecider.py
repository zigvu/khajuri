#!/usr/bin/env python
import time, pdb
import boto.swf.layer2 as swf
import logging, json, yaml
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(process)-8d %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='VideoDecider.log',
                    filemode='a')

config = yaml.load( open( "swf.yaml", "r" ) )
class VideoDecider(swf.Decider):
    domain = config[ 'domain' ]
    task_list = config[ 'task_list' ]
    version = config[ 'version' ]

    def run(self):
      self.version = config[ 'version' ]
      try:
        logging.info( 'Polling for events...' )
        history = self.poll()
        if 'events' in history:
            # Get a list of non-decision events to see what event came in last.
            workflow_events = [e for e in history['events']
                               if not e['eventType'].startswith('Decision')]
            decisions = swf.Layer1Decisions()
            # Record latest non-decision event.
            last_event = workflow_events[-1]
            last_event_type = last_event['eventType']
            for event in workflow_events:
              if event[ 'eventType' ] == 'WorkflowExecutionStarted':
                input = event['workflowExecutionStartedEventAttributes']['input']
            assert input

            if last_event_type == 'WorkflowExecutionStarted':
                logging.info( 'Detecting workflow has started...Scheduling Tasks' )
                decisions.schedule_activity_task('%s-%i' % ('VideoActivity', time.time()),
                   'VideoTestActivity', self.version, task_list=config[ 'task_list'], input=input )
            elif last_event_type == 'ActivityTaskCompleted':
                result = last_event['activityTaskCompletedEventAttributes']['result']
                logging.info( 'Done...%s' % result )
                decisions.complete_workflow_execution()
            elif last_event_type == 'ActivityTaskFailed':
                logging.info( 'Task Failed, mark workflow as failed' )
                reason = last_event['activityTaskFailedEventAttributes'].get('reason')
                details = last_event['activityTaskFailedEventAttributes'].get('details')
                decisions.fail_workflow_execution( reason, details )
            elif last_event_type == 'ActivityTaskTimedOut':
                timeoutType = last_event['activityTaskTimedOutEventAttributes'].get('timeoutType')
                if timeoutType == 'SCHEDULE_TO_START':
                  # Reschedule
                  logging.info( 'Rescheduling task for timeout( SCHEDULE_TO_START )..with input %s' % input )
                  decisions.schedule_activity_task('%s-%i' % ('VideoActivity', time.time()),
                     'VideoTestActivity', self.version, task_list='VideoTaskList',input=input )
                else:
                  logging.info( 'Task timedout, mark workflow as failed' )
                  reason = last_event['activityTaskTimedOutEventAttributes'].get('reason')
                  details = last_event['activityTaskTimedOutEventAttributes'].get('details')
                  decisions.fail_workflow_execution( reason, details )
            else:
                logging.info( 'Unknown Event Occured, mark workflow as failed' )
                reason = last_event['activityTaskTimedOutEventAttributes'].get('reason')
                details = last_event['activityTaskTimedOutEventAttributes'].get('details')
                decisions.fail_workflow_execution( reason, details )
            self.complete(decisions=decisions)
      except Exception as e:
        logging.info( 'Exception: %s' % e )
           
if __name__=="__main__":
  videoDecider = VideoDecider()
  while True:
     videoDecider.run()
