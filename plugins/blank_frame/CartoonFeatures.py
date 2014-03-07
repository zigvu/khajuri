# -*- coding: utf-8 -*-
"""
Features for detecting "Cartoon like Images".
References :

"Detecting Cartoons : A Cast study in automatic video-Genre classification", Ph.D Work. T. Ianeva


@author: Amit
"""

import cv2
import numpy as np
import pdb
import zlib

# Return the average image saturation
# Input: Img- BGR image (CV2 - standard)
# Return Saturation Average

def Get_AvgSat_BrightnessThreshold(Img_BGR,BrightnessThreshold):
    # Convert to HSV
    Img_HSV     = cv2.cvtColor(Img_BGR,cv2.COLOR_BGR2HSV);
    
    # Average Saturation
    AvgSaturation= np.average(Img_HSV[:,:,1]);  #2nd channel, 0 indexing
    
    # Average percent of pixels above specified Brightness threshold 
    Intensity = Img_HSV[:,:,2];
    IntensityAboveThreshold = Intensity[Intensity > BrightnessThreshold];
    ThresholdBrightness = 1.0*IntensityAboveThreshold.size/np.prod(Img_HSV.shape[0:2]);
    
    return AvgSaturation,ThresholdBrightness

# Measure of how compressible is the image
def ImgCompressability(Img_BGR):
    TotalElements = Img_BGR.size;
    Compressed = zlib.compress(Img_BGR,6);  # 6th level compression
    Compression = Compressed.__sizeof__()/Img_BGR.size;
    return Compression
    
# Compute the color histogram
def ColorHist(Img_BGR,NumberOfBins=[3,3,5]):
    # Convert to HSV
    Img_HSV     = cv2.cvtColor(Img_BGR,cv2.COLOR_BGR2HSV);
    # Computer color histogram
    ColorHist = cv2.calcHist([Img_HSV],[0,1,2],None,NumberOfBins,[0,256,0,256,0,256]) # Upper range is exclusive
    ColorHist = ColorHist/np.sum(ColorHist);    # Normalize
    return ColorHist
    
    
# Compute Edge Histogram
# Input: Img_BGR (in BGR), Number of Bins for Magnitude and angles
def EdgeHist(Img_BGR, NumberOfBins=[5,8], EdgeRange =[[0, 10],[-180, 180]],MaxMagnitude = 10 ):
    # Convert to gray scale
    Img_Gray     = cv2.cvtColor(Img_BGR,cv2.COLOR_BGR2GRAY); # Not converting to 
    # Extract gradient with sobel filters
    ddepth = cv2.CV_16S; # Output depth
    dx,dy = 1,1;    # Gradient order
    ImgGrad_X   = cv2.Sobel(Img_Gray,ddepth,1,0).astype('float32'); # Graident in X direction
    ImgGrad_Y   = cv2.Sobel(Img_Gray,ddepth,0,1).astype('float32'); # Graident in Y direction
    # Interestingly if you dont convert to float32, the calculation of gradient is not correct
 
    # Calculate gradient magnitude and angle
    Grad_Magnitude = np.sqrt(np.square(ImgGrad_X)+np.square(ImgGrad_Y));
    Grad_Angle = (180./np.pi)*np.arctan2(ImgGrad_X,ImgGrad_Y);
    Grad_Magnitude[Grad_Magnitude > MaxMagnitude] = MaxMagnitude;
    
    # Calculate gradient magnitude / angle histogram (open cv option is a magnitude faster)
    S = Grad_Magnitude.shape;
    GradHist = np.ndarray((S[0],S[1],2),dtype=Grad_Angle.dtype)
    GradHist[:,:,0] = Grad_Magnitude;
    GradHist[:,:,1] = Grad_Angle;
    H = cv2.calcHist([GradHist],[0,1],None,NumberOfBins,[0,MaxMagnitude,-180,180]);
    H = H/np.sum(H);    # Normalize
    return H
    
    # Numpy option below (x10 slower)
    #H,xe,ye =np.histogram2d(Grad_Magnitude.ravel(),Grad_Angle.ravel(),NumberOfBins,EdgeRange,True)
    #H = np.asarray(H);
    #return H
    
    
def IsCartoon(Img):
    
    Img_HSV     = cv2.cvtColor(Img,cv2.COLOR_BGR2HSV);
    # Average Saturatio
    