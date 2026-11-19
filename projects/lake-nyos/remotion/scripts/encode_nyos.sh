#!/bin/bash
set -e
cd "$(dirname "$0")/.."
D=out/nyos
rm -rf $D/seq; mkdir -p $D/seq; i=0
for a in $(seq 0 100 1500); do
  for f in $(ls $D/c_$a/*.jpeg | sort -V); do ln -s "$PWD/$f" $D/seq/$(printf %05d $i).jpeg; i=$((i+1)); done
done
echo "frames: $i"
ffmpeg -y -loglevel error -framerate 30 -i $D/seq/%05d.jpeg -i /home/user/claude-animated-shorts/projects/lake-nyos/audio/mix.wav \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a aac -b:a 320k -shortest -movflags +faststart out/lake-nyos_1080x1920.mp4
ffprobe -v error -show_entries format=duration:stream=nb_frames,width,height -of compact out/lake-nyos_1080x1920.mp4
cp out/lake-nyos_1080x1920.mp4 public/nyos/base.mp4
npx remotion render src/index.ts NyosCaptioned out/lake-nyos_captions_1080x1920.mp4 --concurrency=3 --crf=16 --x264-preset=slow \
  --audio-codec=aac --audio-bitrate=320k --browser-executable=/opt/pw-browsers/chromium --timeout=300000 --log=error
ffprobe -v error -show_entries format=duration:stream=nb_frames -of compact out/lake-nyos_captions_1080x1920.mp4
