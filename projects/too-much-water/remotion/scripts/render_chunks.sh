#!/bin/bash
# Renders WaterShort at 1080x1920 as JPEG frames, 100 frames per chunk; skips finished chunks; stops after ~100 min.
cd "$(dirname "$0")/.."
START=$(date +%s); TOTAL=1660; STEP=100
mkdir -p out/hd
for ((a=0; a<TOTAL; a+=STEP)); do
  b=$((a+STEP-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  [ -f out/hd/chunk_$a.done ] && continue
  if [ $(( $(date +%s) - START )) -gt 5400 ]; then echo "time budget used, stopping before chunk $a"; exit 0; fi
  t0=$(date +%s)
  rm -rf out/hd/c_$a
  npx remotion render src/index.ts WaterShort out/hd/c_$a --sequence --image-format=jpeg --jpeg-quality=95 \
    --frames=$a-$b --gl=swangle --browser-executable=/opt/pw-browsers/chromium --concurrency=2 --timeout=300000 --log=error \
    > out/hd/log_$a.txt 2>&1 && touch out/hd/chunk_$a.done
  echo "chunk $a-$b: $(( $(date +%s) - t0 )) s, $(ls out/hd/c_$a 2>/dev/null | wc -l) frames, done=$([ -f out/hd/chunk_$a.done ] && echo yes || echo NO)"
done
echo "ALL CHUNKS DONE: $(ls out/hd/*.done | wc -l)"
