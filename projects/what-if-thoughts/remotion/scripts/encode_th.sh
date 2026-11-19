#!/bin/bash
set -e
cd "$(dirname "$0")/.."
rm -rf out/th/seq; mkdir -p out/th/seq; i=0
for a in $(seq 0 100 1900); do
  for f in $(ls out/th/c_$a/*.jpeg | sort -V); do ln -s "$PWD/$f" out/th/seq/$(printf %05d $i).jpeg; i=$((i+1)); done
done
echo "frames: $i"
ffmpeg -y -loglevel error -framerate 30 -i out/th/seq/%05d.jpeg -i /home/user/claude-animated-shorts/projects/what-if-thoughts/audio/mix.wav \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 320k -movflags +faststart out/what-if-thoughts_1080x1920.mp4
ffprobe -v error -show_entries format=duration:stream=nb_frames,width,height -of compact out/what-if-thoughts_1080x1920.mp4
