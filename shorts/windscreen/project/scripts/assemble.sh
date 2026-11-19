#!/bin/bash
# join the parts into one frame-exact 1990-frame picture and mux the final mix
cd "$(dirname "$0")/.."
P=out/parts
ls $P/p_*.mp4 | sort -t_ -k2 -n | sed "s|^|file '$PWD/|; s|$|'|" > out/parts.txt
ffmpeg -v error -y -f concat -safe 0 -i out/parts.txt -i ../audio/mix.wav -map 0:v -map 1:a \
  -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart -shortest out/windscreen_final.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -of csv=p=0 out/windscreen_final.mp4
