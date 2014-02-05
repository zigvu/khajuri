# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 11:25:54 2014

@author: Amit

Testing the Blur Detector
"""

# Inputs -  Directory Path (dont include "\" at the end)
ImgDir = 'C:\Users\Amit\Documents\EvanVideo\SyncBox\Images\Blur'; # This is the directory containing input images
#ImgExt = '*.jpg';   # Extension of the image files
ImgExt = ('*.bmp','*.png')
OutDir = 'C:\Users\Amit\Documents\EvanVideo\SyncBox\Results\Blur';
#ImgDir = 'C:\Users\Amit\Documents\EvanVideo\VideoDownloader\VideosFromAmrit\NonBlanks'
#OutDir = 'C:\Users\Amit\Documents\EvanVideo\VideoDownloader\VideosFromAmrit';
SaveResultsTo_OutDir = 1; # If this is '1', the 'blank' and 'non-blanks' will be saved separately in the 'OutDir'
AddBlurScoresToImg = 0;    # If this is '1', the program will add the entropy and img intensity span score to file


# Needed libs . Make sure they are available in the system (Numpy, Matplotlib, Scikit-image)
import glob
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import BlurDetection as B
import time
from skimage.filter.rank import entropy
import shutil
import os
##############################################################################

## Define a function for creating directory
def CreateDirectory(path):
    import os
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

# Create the output directory if it does not exist
if SaveResultsTo_OutDir == 1:
    # Delete and re create output directoyr
    shutil.rmtree(OutDir+"\YesBlur", ignore_errors=True);
    shutil.rmtree(OutDir+"\NoBlur", ignore_errors=True);
    shutil.rmtree(OutDir+"\MaybeBlur", ignore_errors=True)    
    # Create output directory
    CreateDirectory(OutDir+"\YesBlur")
    CreateDirectory(OutDir+"\NoBlur")
    CreateDirectory(OutDir+"\MaybeBlur")

# Fetch a list of files
#ImgFiles = glob.glob(ImgDir+"/"+ImgExt)
ImgFiles = [];
for ImgType in ImgExt:
    ImgFiles.extend(glob.glob(ImgDir+"/"+ImgType))

# Output variables
IsBlur         = np.zeros((float(len(ImgFiles)),1),dtype=int);
DR  = np.zeros((float(len(ImgFiles)),1),dtype=int);
DR2  = np.zeros((float(len(ImgFiles)),1),dtype=int);

# Iterate through the all the input files and run the blank detector    
k = 0; b = 1;start_time = time.time()
for ImgFile in ImgFiles:    
    
    # Run the blank detector
    Img = mpimg.imread(ImgFile);
    #Img = mpimg.imread(ImgFiles[np.random.randint(0,len(ImgFiles))]);    
    #(IsBlur[k],DR[k],DR2[k]) = B.Is_Blurry(Img)
    IsBlur[k] = B.Is_Blurry(Img);

#    # Save the image to output directory
    if SaveResultsTo_OutDir == 1:
        CopyFrom = ImgFile;

        if IsBlur[k] == 1:
            CopyTo = OutDir+"\\YesBlur\\"+ ImgFile.replace(ImgDir+'\\','');
        elif IsBlur[k] == 2:
            CopyTo = OutDir+"\\MaybeBlur\\" + ImgFile.replace(ImgDir+'\\','');
        else:
            CopyTo = OutDir+"\\NoBlur\\" + ImgFile.replace(ImgDir+'\\','');
            
        if AddBlurScoresToImg == 0:
            shutil.copyfile(CopyFrom,CopyTo);
        else:
            # Plot the image with 'Blank Detector scores' and save
            Img = mpimg.imread(ImgFile);
            fig = plt.figure(k)
            plt.imshow(Img)
            plt.title("Intensity-span: " + str( IntensitySpan[k]) +" , Entropy: "+str(ImgEntropy[k].astype('str')))
            fig.savefig(OutDir+'/'+str(b)+'_'+ImgFile.replace(ImgDir+'\\',''))
            #fig.savefig(OutDir+'/'+(100*BlankScores[k]).astype('str')[0]+'_'+ImgFile.replace(ImgDir+'\\',''))            
            plt.close();
        
    print str(k) + ' of '+ str(len(ImgFiles))+ " Blur: "+str(IsBlur[k]) + " ,("+ str(DR[k])+ ","+str(DR2[k]) +")"
    #print("Elapsed time was %g seconds" % (end_time - start_time))
    k = k+1; 
#    if k > 1000:
#        break;
    if k%100 == 0:
        end_time = time.time();
        print("Elapsed time was %g seconds" % (end_time - start_time))
        

# Plot the final scatter
#plt.figure
#BlankRng = np.flatnonzero(IsBlank > 0);
#NonBlankRng = np.flatnonzero(IsBlank < 1);
#plt.plot(ImgEntropy[BlankRng],IntensitySpan[BlankRng],'or')        ;
#plt.hold('on')
#plt.plot(ImgEntropy[NonBlankRng],IntensitySpan[NonBlankRng],'sk');
#plt.grid('on');
#plt.legend(('Blanks','NonBlanks'),loc=0)
#plt.xlabel('Image Entropy')
#plt.ylabel('Image Intensity Span')