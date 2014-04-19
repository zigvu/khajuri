#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 18:19:05 2014

@author: Amit
"""

# Blurry Image Detection 
import numpy as np
import cv2
import scipy.special as sc
from plugins.Plugin import Plugin
import sys, os

baseScriptDir = os.path.dirname(os.path.realpath(__file__))
class BlurDetection(Plugin):
    
    """ Model Parameters """
    blocksizerow    = 96;
    blocksizecol    = 96;
    blockrowoverlap = 0;
    blockcoloverlap = 0;
    mu_prisparam = os.path.join( baseScriptDir, 'NIQE_mu_prisparam.csv' )
    cov_prisparam = os.path.join( baseScriptDir, 'NIQE_cov_prisparam.csv' )
    mu_prisparam = np.genfromtxt(mu_prisparam,delimiter=',');
    cov_prisparam = np.genfromtxt(cov_prisparam,delimiter=',');
    Threshold = 5.0;
       
    # Precalculation to avoid calculating everytime    
    gam = np.linspace(0.2,10,num=9801);
    r_gam = ((sc.gamma(2/gam))**2) / (sc.gamma(1/gam)*sc.gamma(3/gam));
       
    """Blur plugin"""
    def __init__(self,config):
        self.config = config;
        self.name = "BlurDetection"

    def process(self,frame):
        BlurScore = self.Is_Blurry( cv2.imread( frame.imgName ) );  # Assuming frame is BGR array
        processDecision = True;
        if BlurScore > self.Threshold:     # 1: Blurry, -1: Not Blurry
            processDecision = False;    # Image is blurry
            BlurScore = 1.0;    # Image is blurry
        else:
            BlurScore = -1.0;   # Image is sharp
        # Store results for next lookup
        #frame.vFrame.Is_Blank = IsImgBlank;
        return BlurScore, processDecision; 
        
    # Input: Img is expected to a rgb nd image
    def Is_Blurry(self,Img_BGR):
        # Number of features
        featnum = 18;
        # Convert to Grayscale
        Img_Gray     = cv2.cvtColor(Img_BGR,cv2.COLOR_BGR2GRAY);
        #  Crop the image , so that the outside unused portion is not present       
        BlockRows = np.floor(Img_Gray.shape[0]/self.blocksizerow).astype('int');
        BlockCols = np.floor(Img_Gray.shape[1]/self.blocksizecol).astype('int');
        im = Img_Gray[0:BlockRows*self.blocksizerow, 0:BlockCols*self.blocksizecol].astype('double')
        
        # Prepare the Gaussian kernel
        Sigma = 7.0 / 6.0;  # As suggested in the implementation by authors           
        KSize = 7;
        Gx = cv2.getGaussianKernel(KSize,Sigma);    # Returns 1-D kernel
        Gy = cv2.getGaussianKernel(KSize,Sigma);
        G = Gx * Gy.T;
        
        scaleNum = 2;
        Rows,Cols = np.floor(im.shape[0]/self.blocksizerow).astype('int') , np.floor(im.shape[1]/self.blocksizecol).astype('int');
        feat = np.zeros((Rows*Cols,featnum))
        for itr_scale in (1,2):
            mu = cv2.filter2D(im,cv2.CV_64F,G);            
            sigma = np.sqrt(np.abs(cv2.filter2D(im**2,cv2.CV_64F,G) - mu**2));
            structdis = (im-mu)/(sigma+1);
            
            # Block process to compute a feature set over the images
            blocksizerow    = self.blocksizerow/itr_scale;
            blocksizecol    = self.blocksizecol/itr_scale; 
            FeatureSize = featnum;   # This is the size of the feature vector returned by computeFeatures()
            Rows,Cols = np.floor(structdis.shape[0]/blocksizerow).astype('int') , np.floor(structdis.shape[1]/blocksizecol).astype('int');
            feat_scale = np.zeros((Rows*FeatureSize,Cols));   
            row,col = 0,0;
            for r in np.arange(0,structdis.shape[0]-blocksizerow+1,blocksizerow):
                col = 0;
                for c in np.arange(0,structdis.shape[1]-blocksizecol+1,blocksizecol):
                    Block = structdis[r:r+self.blocksizerow,c:c+self.blocksizecol];
                    #Features = self.computeFeatures(Block);
                    feat_scale[row*FeatureSize:row*FeatureSize+FeatureSize,col] = self.computeFeatures(Block);
                    col = col+1;
                row = row+1;

            feat_scale = feat_scale.reshape((featnum,feat_scale.size/featnum),order='F'); # Order {F} is necessary to make it Matlab like    
            feat_scale = feat_scale.T;

            # Concatenate to feat
            if itr_scale == 1:
                feat = feat_scale
            else:
                feat = np.hstack((feat,feat_scale));
            im = cv2.resize(im,(0,0),fx=0.5,fy=0.5,interpolation=cv2.INTER_CUBIC );
            
        mu_prisparam = self.mu_prisparam;
        cov_prisparam = self.cov_prisparam;
        
        distparam        = feat;
        mu_distparam     = np.nanmean(distparam,axis=0);
            #Create masked array
        ma = np.ma.array(distparam,mask=np.isnan(distparam))
        C = np.ma.cov(ma, rowvar = 0)
        cov_distparam = C.data;
        invcov_param = np.linalg.pinv((cov_prisparam+cov_distparam)/2)
        quality = np.sqrt( (mu_prisparam-mu_distparam).dot(invcov_param.dot((mu_prisparam-mu_distparam).T)));
        return float(quality)

    # From the authors code
    def  computeFeatures(self,structdis):
        # Input is MSCn coefficient
        # Output is 18 dim feature vector
        feat = np.zeros((18,1));    # This is the output
        [alpha,betal,betar] = self.estimateAggdParam(structdis.T.flatten());
        # The first two are overall parameters
        feat[0] = alpha; feat[1] = np.mean([betal,betar]);
        feat = np.array([alpha, np.mean([betal,betar])]);
        shifts = np.asarray([ [0,1],[1,0],[1,1],[1,-1]]);
        for itr_shift in np.arange(0,4,1):
            # Replicate circshift function from matlab using 'roll' function
            shifted_structdis = np.roll(np.roll(structdis,shifts[itr_shift,0],0),shifts[itr_shift,1],1);
            pair = (structdis.T.flatten())*(shifted_structdis.T.flatten());
            [alpha,betal,betar] = self.estimateAggdParam(pair);
            meanparam = (betar-betal)* (sc.gamma(2/alpha) / sc.gamma(1/alpha));
            feat = np.hstack((feat,np.array([alpha, meanparam, betal,betar])));
        feat = feat.T;
        return feat;
            
    # From the authors code
    def estimateAggdParam(self,vec):
        # Scipy gamma function needed for the following   
        # Pre-computed during class initiation.
        gam = self.gam; #np.linspace(0.2,10,num=9801);
        r_gam = self.r_gam; #((sc.gamma(2/gam))**2) / (sc.gamma(1/gam)*sc.gamma(3/gam));
        
        leftstd = np.sqrt(np.mean(vec[vec<-.000001]**2));
        rightstd = np.sqrt(np.mean(vec[vec>.00001]**2));
        
        gammahat = leftstd/rightstd;
        rhat = np.mean(np.abs(vec))**2 / np.mean(vec**2);
        rhatnorm = (rhat*(gammahat**3+1)*(gammahat + 1)) / (gammahat**2+1)**2
        # find where the minimum is occuring
        minpos = np.argmin( (r_gam - rhatnorm)**2);
        alpha = gam[minpos];
        
        betal = leftstd * np.sqrt(sc.gamma(1/alpha) / sc.gamma(3/alpha));
        betar = rightstd * np.sqrt(sc.gamma(1/alpha) / sc.gamma(3/alpha));
        
        return (alpha,betal,betar)

from plugins.Plugin import StandAlonePlugin 
if __name__ == '__main__':
  if len( sys.argv ) < 2:
    print 'Usage %s <img_file>' % sys.argv[ 0 ]
    sys.exit( 1 )
  standAlone = StandAlonePlugin( BlurDetection )
  print standAlone.process( sys.argv[ 1 ] )
