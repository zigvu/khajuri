#!/usr/bin/env python
import boto.swf.layer2 as swf
import logging, sys, pdb
import json, yaml
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(process)-8d %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='VideoWorkflowStarter.log',
                    filemode='a')

config = yaml.load( open( "swf.yaml", "r" ) )
execution = swf.WorkflowType(name=config[ 'workflowtype' ],
                              domain=config[ 'domain' ],
                              version=config[ 'version' ],
                              task_list=config[ 'task_list' ],
                              region='us-west-2' )

#'{ "config.yaml" : "s3url", "video.url": "youtubeUrl" }'
videoInfo = {}
if __name__ == '__main__':
  if len( sys.argv ) < 2:
    print 'Usage %s video.url video.id'
    sys.exit( 1 )
  videoInfo[ config[ 'videoUrlKey' ] ] = sys.argv[ 1 ]
  videoInfo[ config[ 'videoIdKey' ] ] = sys.argv[ 2 ]
  logging.info( 'Starting Video Workflow, inputs %s' % json.dumps( videoInfo ) )
  execution.start(input=json.dumps( videoInfo ) )
