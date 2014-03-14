# -*- coding: utf-8 -*-
"""
Created on Wed Mar 05 22:21:38 2014

@author: Amit

Flat (Blank ) image detection utilizing color histogram



"""

#import cv2  #Open CV: For color histogram
import numpy as np
from sklearn.externals import joblib    # To load SVM parameters
import CartoonFeatures as CF
from plugins.Plugin import Plugin
import cv2
import os

class BlankDetection(Plugin):
    
    # Load parameters for the SVM
    baseScriptDir = os.path.dirname(os.path.realpath(__file__))
    SVM_Filename = os.path.join( baseScriptDir, 'ModelParams', 'BlankModel_ColorHist.mdl' )
    BlankDetectionModel = joblib.load(SVM_Filename)
    
    """Blank plugin"""
    def __init__(self,config):
        self.config = config;
        self.name = "BlankDetection"

    def process(self,frame):
        IsImgBlank, BlankScore = self.Is_Blank( cv2.imread( frame.imgName ));  # Assuming frame is BGR array
        processDecision = False;
        if IsImgBlank < 0:
            processDecision = True;    # Image is not blank
        # Store results for next lookup
        #frame.vFrame.Is_Blank = IsImgBlank;
        return BlankScore, processDecision;            

        
    def Is_Blank(self,Img_BGR):        
        # Parameters
        Color_HistBins = [3,3,5]; # Number of bins for the HSV channel histogram      
        Chunk_Ht = 75; Chunk_Wt = 75; # Size of Pixel chunks for a sliding window
        BlankThreshold = .86;  # If 86 % of image is blank, consider it blank
        
        # 1. First check if overall image is blank        
        # Compute color histogram of overall image
        Xb = CF.ColorHist(Img_BGR,Color_HistBins).flatten();
        # Test if all of image is blank        
        IsImgBlank =     self.BlankDetectionModel.predict(Xb)        
        if IsImgBlank < 0:
            BlankScore = -1;     # Image is globally not blank, set the score to 0
        # If image is not globally sharp, then check the percent of smaller chunks
        else:
            # Iterate through the chunks of the image and then return the percent that is blank           
            row,col = 0,0;
            Rows,Cols = np.floor(Img_BGR.shape[0]/Chunk_Ht) , np.floor(Img_BGR.shape[1]/Chunk_Wt);
            Rows,Cols = int(Rows),int(Cols)
            Chunks = np.zeros([Rows,Cols])
            Img_BlankMask = np.zeros(Img_BGR.shape[0:2])
        
            for r in np.arange(0,Img_BGR.shape[0]-Chunk_Ht+1,Chunk_Ht):
                col = 0;
                for c in np.arange(0,Img_BGR.shape[1]-Chunk_Wt+1,Chunk_Wt):
                    ImgChunk = Img_BGR[r:r+Chunk_Wt,c:c+Chunk_Wt,:];
                    # Calculate features
                    X = CF.ColorHist(ImgChunk,Color_HistBins).flatten();
                    # Is this chunk blank or not
                    B = self.BlankDetectionModel.predict(X);                    
                    # Store result
                    Chunks[row,col] = B;
                    Img_BlankMask[r:r+Chunk_Wt,c:c+Chunk_Wt] = B;
                    #print row,col,Chunks.shape
                    col += 1;
                row += 1;
            BlankScore = 1-1.0*np.flatnonzero(Chunks < 0).size/Chunks.size;
            
            if BlankScore > BlankThreshold:    # If less than 10 % is blank consider blank
                IsImgBlank = 1;
            else:
                IsImgBlank = -1;
        
            
        return  IsImgBlank, BlankScore;

    
