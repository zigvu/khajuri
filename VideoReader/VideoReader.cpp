#include "VideoFrameReader.h"

int main(int argc, char *argv[]) {
  if(argc < 2) {
    printf("Please provide a movie file\n");
    return -1;
  }

	char fileName[1024];
  sprintf(fileName, "frame"); 

  // Note: Exception handling not currently done
  // try {
  //   VideoFrameGrabber vf(5, argv[1]);
  // } catch (std::exception ex){
  //   std::cout << ex.what() << std::endl;
  //   return -1;
  // }
  VideoFrameReader vf(60, 60, argv[1]);
  vf.startThreads();

  int seekFrameNumber = -2;
  printf("Please type in the frame number to seek to:\n");
  while(seekFrameNumber != -1){
  	scanf("%d",&seekFrameNumber);
  	printf(">>Seeking Frame: %d\n", seekFrameNumber);
  	
  	// NOTE: uncomment this to not save frame for faster testing:
  	// VideoFrame *retVideoFrame = vf.getFrameWithFrameNumber(seekFrameNumber);
  	// if(retVideoFrame != NULL){
  	// 	printf(">>Seeking Frame Return success: %lld\n", (long long)retVideoFrame->getFrameNumber());
  	// }

  	int retVideoFrame2 = vf.saveFrameWithFrameNumber(seekFrameNumber, fileName);
  	if(retVideoFrame2 != -1){
  		printf(">>Saved frame: %d\n", seekFrameNumber);
  	}
  }
  vf.joinThreads();

  return 0;
}