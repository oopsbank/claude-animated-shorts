#!/bin/bash
set -e
cd "$(dirname "$0")/.."
rm -rf out/nd/seq; mkdir -p out/nd/seq; i=0
for a in $(seq 0 100 1600); do
  for f in $(ls out/nd/c_$a/*.jpeg | sort -V); do ln -s "$PWD/$f" out/nd/seq/$(printf %05d $i).jpeg; i=$((i+1)); done
done
echo "frames: $i"
ffmpeg -y -loglevel error -framerate 30 -i out/nd/seq/%05d.jpeg -i /home/user/claude-animated-shorts/projects/no-dying-town/audio/mix.wav \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 320k -movflags +faststart out/no-dying-town_1080x1920.mp4
ffprobe -v error -show_entries format=duration:stream=nb_frames,width,height -of compact out/no-dying-town_1080x1920.mp4
