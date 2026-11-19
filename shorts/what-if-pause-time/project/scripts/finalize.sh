#!/bin/bash
# put the thumbnail in front as the first 3 frames (0.1 s), shift the audio by the same 0.1 s:
#   (subtitled version only)
#   out/pause_content_subs.mp4 -> ../final/pause_time_final_subs.mp4
cd "$(dirname "$0")/.."
for pair in "out/pause_content_subs.mp4 ../final/pause_time_final_subs.mp4"; do
  set -- $pair
  ffmpeg -v error -y -loop 1 -framerate 30 -t 0.1 -i ../final/pause_time_thumbnail.png -i $1 \
    -filter_complex "[0:v]scale=1080:1920,format=yuv420p,setsar=1[t];[1:v]setsar=1[m];[t][m]concat=n=2:v=1:a=0[v];[1:a]adelay=100|100,apad[a]" \
    -map "[v]" -map "[a]" -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -r 30 -c:a aac -b:a 256k -shortest -movflags +faststart $2
  ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $2
  ffprobe -v error -show_entries format=duration -of csv=p=0 $2
done
