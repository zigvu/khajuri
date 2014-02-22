# Blank Image Detection 
import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from skimage.color import rgb2gray
from plugins.Plugin import Plugin

class BlankDetection(Plugin):
	"""Blank Plugin."""
	def __init__(self, config):
		self.config = config
		self.name = "BlankDetection"
		# Access config Parameters
		self.threshold = self.config[ 'threshold' ]

	def process(self, frame):
                result = self.Is_Blank( frame.imgName )
		processDecision = False
		if result[0] == 0:
			processDecision = True
		# Storing Computed results for next look up
		frame.Is_Bank = result[ 0 ]
		return result[1], processDecision

        def Is_Blank(self,Img_FileName):
            # Read the image file
            Img = mpimg.imread(Img_FileName);    
            # Convert to grayscale
            Img_Gray = rgb2gray(Img);
            # Flatten 2D Array to single Array
            Img_Flat = Img_Gray.flatten();
            # Compute Histogram
            Hist, Bin_edges = np.histogram(Img_Flat,bins=100,density="TRUE")  
            # Normalize the Histogram
            HistNorm = Hist/np.sum(Hist)
            # Find the percentage of bins that account for over 0.4 % (1/255)
            Crit = 0.0015
            NonZeroRng = np.flatnonzero(HistNorm > Crit)
            
            
            # 1. Calculate ImgBandWidth (Make sure to convert to float by multiplying by 1.0)
            ImgIntBandWidth =  1.0*NonZeroRng.size/HistNorm.size;
            # Bin Centers
        
        
            # Calculate entropy 
            BinProb = Hist/np.sum(Hist);
                # Remove zeros
            rng = np.flatnonzero(BinProb > 0);
            BinProb = BinProb[rng];
            Entropy = 1.0*-np.sum(BinProb*np.log2(BinProb));
            
            # Display the image
        #    Bin_size = Bin_edges[1] - Bin_edges[0]    
        #    Bin_centers = Bin_edges[0:Hist.size]+Bin_size/2;
        #    plt.figure(figsize=[18,6])
        #    plt.subplot(121)
        #    plt.imshow(Img_Gray)
        #    plt.subplot(122)
        #    plt.plot(Bin_centers,HistNorm,'r-+')   
        #    plt.grid();
        #    plt.axis('tight')
        #    plt.ylim((0.0, 0.1))
        #    plt.hold(True)
        #    plt.plot(Bin_centers,Crit*np.ones(Bin_centers.shape),'--k')
            
            # Threshold for blank images
            Blank = 0;
            
            if ImgIntBandWidth < 0.25 and Entropy < 2.25:  # This will need to be tuned with more images
                Blank = 1;
            else:
                Blank = 0;
            
            return Blank,ImgIntBandWidth,Entropy
