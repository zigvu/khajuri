#!/bin/bash
rm -rf /tmp/VideoFrames/*
mkdir -p /tmp/VideoFrames/
for i in `seq 0 99`; do
    convert -size 1024x720 -background lightblue -fill blue -font Courier -pointsize 200 label:$i /tmp/VideoFrames/img$i.jpg
done
ffmpeg -f image2 -i /tmp/VideoFrames/img%d.jpg -b 800k /tmp/VideoFrames/out.mp4
rm /tmp/VideoFrames/*.jpg
echo "Video created in /tmp/VideoFrames folder"
