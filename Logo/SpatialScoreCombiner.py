# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 07:16:35 2014

@author: amit.bohara

Combine detector score to output frame decision

"""

# Imports
import numpy as np
import pdb
import math

class SpatialScoreCombiner():
    
    #def __init__(self):
        
        
    def processFrame(self,PredictorObj,Parameters,frameId):
        # Parse parameters
        
        scales = PredictorObj.getScalingFactors();
        classes = PredictorObj.getClassIds();
        numClasses = len(classes);
        # For allowing multi class , scale detetor threshold by number of classes (Works as expected for two classification)
        DetectorThresh = Parameters['DetectorThresh']/(numClasses-1);
        HitThresh = Parameters['HitThresh'];
        # iterate through scales and mark the patches
        for classId in classes:
            # Initialize large image mask to hold the heat map
            imMask = np.zeros((2000,2000),dtype=np.int8);
            imRows = 0; imCols = 0;     # The image size will be updated 
            
            for scale in scales:
                # Get patches for this frame,scale
                Patches = PredictorObj.getPatches(frameId,scale);
                # Iterate through the patches and update mask
                
                for patchId in Patches.keys():
                    RowStart    = round(Patches[patchId]['y']/scale);
                    ColStart    = round(Patches[patchId]['x']/scale);
                    RowEnd      = math.floor(RowStart + Patches[patchId]['height']/scale);   
                    ColEnd      = math.floor(ColStart + Patches[patchId]['width']/scale);
                    PatchScore  = PredictorObj.getScore(frameId,patchId,classId,scale);
                    if PatchScore > DetectorThresh:
                        imMask[RowStart:RowEnd,ColStart:ColEnd] += 1;
                    # Keep track of how big thsi image is. That way we dont have to read the image to output heat map
                    imRows = max([imRows,RowEnd]);
                    imCols = max([imCols,ColEnd]);
            
            # Save result for this class
            classScore = (imMask.max() >= HitThresh)*1.0;
            PredictorObj.saveScore(frameId,classId,classScore)
            #if classScore > 0.5:
             #   print str(frameId) + " positive on class " + str(classId)
