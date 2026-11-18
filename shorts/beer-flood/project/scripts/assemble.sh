#!/bin/bash
# splice the parts + review patches into one frame-exact 1948-frame picture, mux the final mix
cd "$(dirname "$0")/.."
P=out/parts
ffmpeg -v error -y \
  -i $P/fix_0.mp4 -i $P/p_0.mp4 -i $P/fix_386.mp4 -i $P/p_500.mp4 -i $P/p_1000.mp4 -i $P/p_1500.mp4 \
  -i ../audio/mix.wav -filter_complex "\
[0:v]trim=start_frame=0:end_frame=132,setpts=PTS-STARTPTS[a];\
[1:v]trim=start_frame=132:end_frame=386,setpts=PTS-STARTPTS[b];\
[2:v]trim=start_frame=0:end_frame=117,setpts=PTS-STARTPTS[c];\
[3:v]trim=start_frame=3:end_frame=500,setpts=PTS-STARTPTS[d];\
[4:v]setpts=PTS-STARTPTS[e];[5:v]setpts=PTS-STARTPTS[f];\
[a][b][c][d][e][f]concat=n=6:v=1:a=0,fps=30[v]" \
  -map "[v]" -map 6:a:0 -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart -shortest \
  out/beer_flood_final.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -of csv=p=0 out/beer_flood_final.mp4
