#!/bin/bash
rm /tmp/VideoFrames/*
mkdir -p /tmp/VideoFrames/
for i in `seq 1 100`; do
    convert -size 800x600 -background lightblue -fill blue -font Courier -pointsize 200 label:$i /tmp/VideoFrames/img$i.jpg
done
cd /tmp/VideoFrames/
ffmpeg -f image2 -i /tmp/VideoFrames/img%d.jpg -b 800k /tmp/VideoFrames/out.mp4
ffmpeg -f image2 -i /tmp/VideoFrames/img%d.jpg -b 800k /tmp/VideoFrames/out.mpg
