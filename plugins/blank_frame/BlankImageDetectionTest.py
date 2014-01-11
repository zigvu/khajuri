# -*- coding: utf-8 -*-
"""
Created on Sat Jan 04 14:34:18 2014
@author: Amit

Set The inputs below
"""

# Inputs -  Directory Path (dont include "\" at the end)
ImgDir = 'C:\Users\Amit\Documents\EvanVideo\VideoDownloader\AllImages'; # This is the directory containing input images
ImgExt = '*.jpg';   # Extension of the image files
OutDir = 'C:\Users\Amit\Documents\EvanVideo\BlankDetectionResults';
SaveResultsTo_OutDir = 1; # If this is '1', the 'blank' and 'non-blanks' will be saved separately in the 'OutDir'
AddBlankScoresToImg = 0;    # If this is '1', the program will add the entropy and img intensity span score to file


# Needed libs . Make sure they are available in the system (Numpy, Matplotlib, Scikit-image)
import glob
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import BlankImageDetection as B
import time
from skimage.filter.rank import entropy
import shutil
##############################################################################

## Define a function for creating directory
def CreateDirectory(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

# Create the output directory if it does not exist
if SaveResultsTo_OutDir == 1:
    # Delete and re create output directoyr
    shutil.rmtree(OutDir+"\Blanks", ignore_errors=True)    
    shutil.rmtree(OutDir+"\NonBlanks", ignore_errors=True)    
    # Create output directory
    CreateDirectory(OutDir+"\Blanks")
    CreateDirectory(OutDir+"\NonBlanks")

# Fetch a list of files
ImgFiles = glob.glob(ImgDir+"/"+ImgExt)

# Output variables
IntensitySpan   = np.zeros((float(len(ImgFiles)),1));
ImgEntropy      = np.zeros((float(len(ImgFiles)),1));
IsBlank         = np.zeros((float(len(ImgFiles)),1));
    
# Iterate through the all the input files and run the blank detector    
k = 0; b = 1;start_time = time.time()
for ImgFile in ImgFiles:    

    # Run the blank detector
    IsBlank[k], IntensitySpan[k],ImgEntropy[k] = B.Is_Blank(ImgFile)

#    # Save the image to output directory
    if SaveResultsTo_OutDir == 1:
        CopyFrom = ImgFile;

        if IsBlank[k] == 1:
            CopyTo = OutDir+"\\Blanks\\"+ ImgFile.replace(ImgDir+'\\','');
        else:
            CopyTo = OutDir+"\\NonBlanks\\" + ImgFile.replace(ImgDir+'\\','');
            
        if AddBlankScoresToImg == 0:
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
        
    print str(k) + ' of '+ str(len(ImgFiles));
    k = k+1; 
#    if k > 5000:
#        break;
    if k%100 == 0:
        end_time = time.time();
        print("Elapsed time was %g seconds" % (end_time - start_time))
        

# Plot the final scatter
plt.figure
BlankRng = np.flatnonzero(IsBlank > 0);
NonBlankRng = np.flatnonzero(IsBlank < 1);
plt.plot(ImgEntropy[BlankRng],IntensitySpan[BlankRng],'or')        ;
plt.hold('on')
plt.plot(ImgEntropy[NonBlankRng],IntensitySpan[NonBlankRng],'sk');
plt.grid('on');
plt.legend(('Blanks','NonBlanks'),loc=0)
plt.xlabel('Image Entropy')
plt.ylabel('Image Intensity Span')