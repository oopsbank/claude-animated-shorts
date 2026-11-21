#!/usr/bin/env bash
# Put the thumbnail in the first 3 frames (0.1 s) of the final video and delay the audio by 0.1 s, so the cover
# is the first frame platforms show (channel convention, see PIPELINE.md › Publishing).
# usage: tools/add_cover.sh video.mp4 thumbnail.png out.mp4
set -euo pipefail
ffmpeg -v error -y -loop 1 -framerate 30 -t 0.1 -i "$2" -i "$1" -filter_complex \
  "[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[c];[1:v]setsar=1,format=yuv420p[m];[c][m]concat=n=2:v=1:a=0[v];[1:a]adelay=100:all=1[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -movflags +faststart "$3"
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames,width,height -of csv=p=0 "$3"
