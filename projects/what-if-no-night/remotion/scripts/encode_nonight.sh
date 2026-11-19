#!/bin/bash
# frames -> scene mp4 (with mix) -> captioned mp4 -> both with the cover as the first 3 frames (audio delayed 0.1 s)
set -e
cd "$(dirname "$0")/.."
D=out/nonight; A=/home/user/claude-animated-shorts/projects/what-if-no-night/audio/mix.wav
rm -rf $D/seq; mkdir -p $D/seq; i=0
for a in $(seq 0 100 1800); do
  for f in $(ls $D/c_$a/*.jpeg | sort -V); do ln -s "$PWD/$f" $D/seq/$(printf %05d $i).jpeg; i=$((i+1)); done
done
echo "frames: $i"
ffmpeg -y -loglevel error -framerate 30 -i $D/seq/%05d.jpeg -i $A -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -c:a aac -b:a 320k -shortest -movflags +faststart out/nonight_scene.mp4
cp out/nonight_scene.mp4 public/nonight/base.mp4
npx remotion render src/index.ts NoNightCaptioned out/nonight_scene_captions.mp4 --concurrency=3 --crf=16 --x264-preset=slow \
  --audio-codec=aac --audio-bitrate=320k --browser-executable=/opt/pw-browsers/chromium --timeout=300000 --log=error
for v in scene scene_captions; do
  o=${v/scene/what-if-no-night_1080x1920}; o=${o/_captions/}; [ $v = scene_captions ] && o=what-if-no-night_captions_1080x1920
  ffmpeg -y -loglevel error -loop 1 -framerate 30 -t 0.1 -i out/nonight_thumb.jpg -i out/nonight_$v.mp4 \
    -filter_complex "[0:v]scale=1080:1920,format=yuv420p,setsar=1[t];[1:v]setsar=1[v];[t][v]concat=n=2:v=1:a=0[vv];[1:a]adelay=100|100[aa]" \
    -map "[vv]" -map "[aa]" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 320k -movflags +faststart out/$o.mp4
  ffprobe -v error -show_entries format=duration:stream=nb_frames -of compact out/$o.mp4
done
