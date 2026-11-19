#!/bin/bash
# Renders $COMP at 1080x1920 as JPEG frames, 100 frames per chunk; skips finished chunks; stops after ~100 min.
cd "$(dirname "$0")/.."
START=$(date +%s); TOTAL=${TOTAL:-1660}; COMP=${COMP:-WaterShort}; OUT=${OUT:-out/hd}; STEP=100
mkdir -p $OUT
for ((a=0; a<TOTAL; a+=STEP)); do
  b=$((a+STEP-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  [ -f $OUT/chunk_$a.done ] && continue
  if [ $(( $(date +%s) - START )) -gt 6900 ]; then echo "time budget used, stopping before chunk $a"; exit 0; fi
  t0=$(date +%s)
  rm -rf $OUT/c_$a
  npx remotion render src/index.ts $COMP $OUT/c_$a --sequence --image-format=jpeg --jpeg-quality=95 \
    --frames=$a-$b --gl=swangle --browser-executable=/opt/pw-browsers/chromium --concurrency=2 --timeout=300000 --log=error \
    > $OUT/log_$a.txt 2>&1 && touch $OUT/chunk_$a.done
  echo "chunk $a-$b: $(( $(date +%s) - t0 )) s, $(ls $OUT/c_$a 2>/dev/null | wc -l) frames, done=$([ -f $OUT/chunk_$a.done ] && echo yes || echo NO)"
done
echo "ALL CHUNKS DONE: $(ls $OUT/*.done | wc -l)"
