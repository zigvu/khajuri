# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 18:19:05 2014

@author: Amit
"""

# Blurry Image Detection 
import numpy as np
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
import pdb

def BlockDiffVariance(ImgBlock,Orientation="Horizontal"):
    if Orientation == "Horizontal":
        BlockDiff = np.diff(ImgBlock,1,1);
    else:   # Vertical gradient
        BlockDiff = np.diff(ImgBlock,1,0);
    return np.var(BlockDiff.flatten());
    
    
# This is the bulk of the blur detection adapted from 
# "Effcient Method of Detecting Blurry Images", Elena Tsomko, Hyoung Joong Kim, Joonki Paik, In-Kwon Yeo"
def ImageBlockVariance(ImgGray,Orientation="Horizontal"):
    #Inputs : ImgGray is the image grayscale intensity
    #        Orientation is whether the variance is to be computer on a vertical or horizontal scan
    
    # Parameters (I am not sure if these need tuned with different video sizes)
    BlockRowSize,BlockColSize = 100,100;    # Image block analyzed at a time
    #BlockRowSize,BlockColSize = 50,50;    # Image block analyzed at a time
    T1,T2 = 40,20;  #
    t1,t2 = 10,10;  #
    V1,V2 = 0.75, 0.90; #
    
    # Output variables
    Blur = 0; # 1: Blurry, 2: In between, 3: Not blurry
    DecisionRoute = 0;
    ContinueTests = 0;
    # Iterate blockwise through the image and compute 1st order gradient variance
    Sz = ImgGray.shape; 
    ri,ci = 0,0;    # row and column index
    BlockVar = np.zeros((100,100));     # Init to some large size
    for r in np.arange(0,Sz[0]-BlockRowSize,BlockRowSize):
        for c in np.arange(0,Sz[1]-BlockColSize,BlockColSize):
            Block = ImgGray[r:r+BlockRowSize, c:c+BlockColSize];
            # Calculate block gradient either horizontally or vertically
            BlockVar[ri,ci]   = BlockDiffVariance(Block,Orientation)
            ci = ci+1;
        ri = ri+1;
    BlockVar= BlockVar[0:ri-1,0:ci-1];
    # Decision tree for blur checks
    GlobalImageVar = BlockDiffVariance(ImgGray,Orientation); 
    
    #pdb.set_trace()      
    # 1. Is Image Globally sharp    
    if GlobalImageVar > T1:
        Blur,DecisionRoute = 3,1;   # Globally sharp
        return Blur,DecisionRoute;
    # 2. Test for possible global blurriness
    if GlobalImageVar <= T2:
        # 2.a. Number of blocks with variance less than 't2'
        Rs_t2 = len(np.flatnonzero(BlockVar.flatten() < t2))*1.0;
        if 1.0*Rs_t2/BlockVar.size > V2:
            Blur,DecisionRoute = 1,2;   # Globally blurry    
            return Blur,DecisionRoute;
        else:
            # Continue with more Tests
            ContinueTests = 1;
    # 3. Test for possible global sharpness or in-between image quality
    if GlobalImageVar > T2 or ContinueTests == 1:
        # Number of blocks with local variance less than 't1'
        Rs_t1 = len(np.flatnonzero(BlockVar.flatten() < t1))*1.0;
        if 1.0*Rs_t1/BlockVar.size < V1:
            Blur,DecisionRoute = 3,3;
            return Blur,DecisionRoute;
        else:
            Blur,DecisionRoute = 2,4;
            return Blur,DecisionRoute;
            
    # Return default
    return Blur,DecisionRoute;
# Input: Img is expected to a rgb nd image
def Is_Blurry(Img):
       
    # Convert to grayscale
    Img_Gray = rgb2gray(Img)*255.0;
    # Flatten 2D Array to single Array
    Img_Flat = Img_Gray.flatten();
    #pdb.set_trace();
    Blur_Horz,DR1 = ImageBlockVariance(Img_Gray,"Horizontal");
    Blur_Vert,DR2 = ImageBlockVariance(Img_Gray,"Vertical");
    #DR1,DR2 = int(DR1),int(DR2)
    Blur = min( (Blur_Horz, Blur_Vert));
    #return (Blur,DR1,DR2)
    return Blur
