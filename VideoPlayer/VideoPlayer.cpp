// Play Videos
#ifdef __cplusplus
  #define __STDC_CONSTANT_MACROS
  #ifdef _STDINT_H
    #undef _STDINT_H
  #endif
  extern "C" {
    #include <stdint.h>
    #include <libavcodec/avcodec.h>
    #include <libavformat/avformat.h>
    #include <libswscale/swscale.h>
  }
#endif

#include <iostream>
#include <vector>
using namespace std;

#include <SDL.h>
#include <SDL_ttf.h>

#ifdef __MINGW32__
#undef main /* Prevents SDL from overriding main() */
#endif

#include <stdio.h>
#include <assert.h>

vector< AVFrame *> myPackets;

// TTF_Init() must be called before using this function.
// Remember to call TTF_Quit() when done.
void drawText(SDL_Surface* screen, char* string, int size, int x, int y, int fR, int fG, int fB,
    int bR, int bG, int bB) {
  TTF_Font* font = TTF_OpenFont("/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf", size);
  SDL_Color foregroundColor = { fR, fG, fB };
  SDL_Color backgroundColor = { bR, bG, bB };
  SDL_Surface* textSurface = TTF_RenderText_Shaded(font, string, foregroundColor, backgroundColor);
  SDL_Rect textLocation = { x, y, 0, 0 };
  SDL_BlitSurface(textSurface, NULL, screen, &textLocation);
  SDL_FreeSurface(textSurface);
  TTF_CloseFont(font);
}

void save( const AVFrame * pFrame ) {
  AVFrame *dst = av_frame_alloc();
  memset(dst, 0, sizeof(*dst));
  int w = pFrame->width, h = pFrame->height;
  enum PixelFormat src_pixfmt = (enum PixelFormat)pFrame->format;
  int numBytes = avpicture_get_size(src_pixfmt, w, h);
  uint8_t *buffer = (uint8_t *)av_malloc(numBytes*sizeof(uint8_t));
  avpicture_fill( (AVPicture *)dst, buffer, src_pixfmt, w, h);
  // Copy data from the 3 input buffers
  //memcpy(dst->data[0], pFrame->data[0], dst->linesize[0] * dst->height);
  //memcpy(dst->data[1], pFrame->data[1], dst->linesize[1] * dst->height / 2);
  //memcpy(dst->data[2], pFrame->data[2], dst->linesize[2] * dst->height / 2);
  struct SwsContext *convert_ctx=NULL;
  convert_ctx = sws_getContext(w, h, src_pixfmt, w, h, src_pixfmt,
      SWS_BILINEAR, NULL, NULL, NULL);
  sws_scale(convert_ctx, pFrame->data, pFrame->linesize, 0, h,
      dst->data, dst->linesize);
  sws_freeContext(convert_ctx);
  myPackets.push_back( dst );
  fprintf(stderr, "Done saving frame, size: %ld...\n", myPackets.size() );
}

SDL_Overlay     *bmp = NULL;
SDL_Surface     *screen = NULL;
SDL_Rect        rect;
AVCodecContext  *pCodecCtx = NULL;
SwsContext *sws_ctx = NULL;


void displayFrameAt( int displayFrameNum ) {
  char frameLabel[20];
  AVFrame *pFrame = myPackets[ displayFrameNum ];
  assert( pFrame != NULL );
  SDL_LockYUVOverlay(bmp);

  AVPicture pict;
  // Add frame numbers
  pict.data[0] = bmp->pixels[0];
  pict.data[1] = bmp->pixels[2];
  pict.data[2] = bmp->pixels[1];

  pict.linesize[0] = bmp->pitches[0];
  pict.linesize[1] = bmp->pitches[2];
  pict.linesize[2] = bmp->pitches[1];

  // Convert the image into YUV format that SDL uses
  sws_scale
    (
     sws_ctx, 
     (uint8_t const * const *)pFrame->data, 
     pFrame->linesize, 
     0,
     pCodecCtx->height,
     pict.data,
     pict.linesize
    );


  SDL_UnlockYUVOverlay(bmp);

  rect.x = 0;
  rect.y = 0;
  rect.w = pCodecCtx->width;
  rect.h = pCodecCtx->height;
  SDL_DisplayYUVOverlay(bmp, &rect);
  sprintf( frameLabel, "Frame: %05d", displayFrameNum );
  drawText( screen, 
      frameLabel,
      24,
      30, 30,
      0, 100, 0,
      255, 255, 255 );
  SDL_UpdateRect(screen, 30, 30, 30, 30 );
}

int main(int argc, char *argv[]) {
  AVFormatContext *pFormatCtx = NULL;
  int             i, videoStream;
  AVCodec         *pCodec = NULL;
  AVFrame         *pFrame = NULL; 
  AVPacket        packet;
  int             frameFinished;
  int            paused = 0;
  //float           aspect_ratio;

  AVDictionary    *optionsDict = NULL;

  SDL_Event       event;

  if(argc < 2) {
    fprintf(stderr, "Usage: %s <file>\n", argv[ 0 ] );
    exit(1);
  }
  // Register all formats and codecs
  av_register_all();

  if(SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_TIMER)) {
    fprintf(stderr, "Could not initialize SDL - %s\n", SDL_GetError());
    exit(1);
  }

  // Open video file
  if(avformat_open_input(&pFormatCtx, argv[1], NULL, NULL)!=0)
    return -1; // Couldn't open file

  // Retrieve stream information
  if(avformat_find_stream_info(pFormatCtx, NULL)<0)
    return -1; // Couldn't find stream information

  // Dump information about file onto standard error
  av_dump_format(pFormatCtx, 0, argv[1], 0);

  // Find the first video stream
  videoStream=-1;
  for(i=0; i<pFormatCtx->nb_streams; i++)
    if(pFormatCtx->streams[i]->codec->codec_type==AVMEDIA_TYPE_VIDEO) {
      videoStream=i;
      break;
    }
  if(videoStream==-1)
    return -1; // Didn't find a video stream

  // Get a pointer to the codec context for the video stream
  pCodecCtx=pFormatCtx->streams[videoStream]->codec;

  // Find the decoder for the video stream
  pCodec=avcodec_find_decoder(pCodecCtx->codec_id);
  if(pCodec==NULL) {
    fprintf(stderr, "Unsupported codec!\n");
    return -1; // Codec not found
  }

  // Open codec
  if(avcodec_open2(pCodecCtx, pCodec, &optionsDict)<0)
    return -1; // Could not open codec

  // Allocate video frame
  pFrame=av_frame_alloc();

  // Make a screen to put our video
#ifndef __DARWIN__
  screen = SDL_SetVideoMode(pCodecCtx->width, pCodecCtx->height, 0, 0);
#else
  screen = SDL_SetVideoMode(pCodecCtx->width, pCodecCtx->height, 24, 0);
#endif
  if(!screen) {
    fprintf(stderr, "SDL: could not set video mode - exiting\n");
    exit(1);
  }


  SDL_WM_SetCaption("SDL Tutorial", "SDL Tutorial");
  if (TTF_Init() != 0) {
    fprintf( stderr, "TTF_Init() failed\n" );
    SDL_Quit();
    exit(1);
  }

  // Allocate a place to put our YUV image on that screen
  bmp = SDL_CreateYUVOverlay(pCodecCtx->width,
      pCodecCtx->height,
      SDL_YV12_OVERLAY,
      screen);

  sws_ctx =
    sws_getContext
    (
     pCodecCtx->width,
     pCodecCtx->height,
     pCodecCtx->pix_fmt,
     pCodecCtx->width,
     pCodecCtx->height,
     PIX_FMT_YUV420P,
     SWS_BILINEAR,
     NULL,
     NULL,
     NULL
    );

  // Read frames and push into vector
  // Display frames from the vector
  int generatedFrameNum=-1;
  int displayFrameNum=0;
  for( ;; ) {
    if( av_read_frame(pFormatCtx, &packet) >= 0 ) {
      if(packet.stream_index==videoStream) {
        // Decode video frame
        avcodec_decode_video2(pCodecCtx, pFrame, &frameFinished, 
            &packet);
        if(frameFinished) {
          save( pFrame );
          generatedFrameNum++;
        }
      }
    }

    SDL_PollEvent(&event);
    switch(event.type) {
      case SDL_QUIT:
        SDL_Quit();
        exit(0);
        break;
      case SDL_MOUSEBUTTONDOWN:
        fprintf (stderr, "Mouse clicked. Toggle Pause\n" );
        paused = 1;
        break;
      case SDL_KEYDOWN:
        switch( event.key.keysym.sym) {
          case SDLK_p:
            paused = 1;
            fprintf( stderr, "Pause\n" );
            break;
          case SDLK_r:
            paused = 0;
            fprintf( stderr, "Resume\n" );
            break;
          case SDLK_h:
            paused = 1;
            fprintf( stderr, "====================\n" );
            fprintf( stderr, "Help for VideoPlayer\n" );
            fprintf( stderr, "h - help, p - paused, r - resume, s - start over\n" );
            fprintf( stderr, "k/<-- - back 1 frame, l/--> - forward one frame, o - turn on localization, t - heatmap on\n" );
            fprintf( stderr, "q - quit\n" );
            fprintf( stderr, "====================\n" );
            break;
          case SDLK_q:
            fprintf( stderr, "Quiting\n" );
            SDL_Quit();
            exit(0);
            break;
          case SDLK_s:
            fprintf( stderr, "Starting again\n" );
            paused = 0;
            displayFrameNum = 0;
            break;
          case SDLK_k:
          case SDLK_LEFT:
            paused = 1;
            displayFrameNum--;
            if ( displayFrameNum < 0 ) {
              displayFrameNum = 0;
            }
            fprintf( stderr, "Stepping back 1 frame to %d\n", displayFrameNum );
            displayFrameAt( displayFrameNum );
            break;
          case SDLK_l:
          case SDLK_RIGHT:
            paused = 1;
            displayFrameNum++;
            if ( displayFrameNum > generatedFrameNum ) {
              displayFrameNum = generatedFrameNum;
            }
            fprintf( stderr, "Stepping forward 1 frame to %d\n", displayFrameNum );
            displayFrameAt( displayFrameNum );
            break;
          default:
            break;
        }

      default:
        break;
    }
    if( !paused && generatedFrameNum >= displayFrameNum ) {
       displayFrameAt( displayFrameNum );
      displayFrameNum++;
    }
  }

  // Free the packet that was allocated by av_read_frame
  av_free_packet(&packet);

  // Free the YUV frame
  av_free(pFrame);
  
  // Close the codec
  avcodec_close(pCodecCtx);
  
  // Close the video file
  avformat_close_input(&pFormatCtx);
  
  return 0;
}

