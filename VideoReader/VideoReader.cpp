#include <stdlib.h>
#include <unistd.h>
#include "VideoFrameReader.h"

int main(int argc, char *argv[]) {
  if(argc < 4) {
    printf("Usage: FrameCreator <videoFileName> <nthFrame> <outputFolder>\n");
    printf("    <videoFileName> : File name of the video\n");
    printf("    <nthFrame>      : Dump every nth frame\n");
    printf("    <outputFolder>  : Folder to put all dumped frames\n");
    return -1;
  }

  char fileName[1024];
  char command[1024];
  int nthFrame = atoi(argv[2]);

  // Note: Exception handling not currently done
  // try {
  //   VideoFrameGrabber vf(5, argv[1]);
  // } catch (std::exception ex){
  //   std::cout << ex.what() << std::endl;
  //   return -1;
  // }
  VideoFrameReader vf(60, 60, argv[1]);
  vf.startThreads();


  int seekFrameNumber = 1;
  int seeReturnValue = 0;

  sleep(2);
  sprintf(command, "mkdir -p %s", argv[3]);
  system(command);

  while(seeReturnValue == 0){
    sprintf(fileName, "%s/%s_frame_%d.png", argv[3],basename(argv[3]), seekFrameNumber);
    printf(">>Saving Frame: %d at %s\n", seekFrameNumber, fileName );

    seeReturnValue = vf.savePngWithFrameNumber(seekFrameNumber, fileName);
    seekFrameNumber = seekFrameNumber + nthFrame;
  }

  vf.joinThreads();
  return 0;
}
