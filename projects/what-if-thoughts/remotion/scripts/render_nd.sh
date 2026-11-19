#!/bin/bash
# Renders ${COMP:-NoDieShort} (COMP/TOTAL/OUT overridable) at 1080x1920 as JPEG frames, 100 frames per chunk; skips finished chunks; stops after ~100 min.
cd "$(dirname "$0")/.."
START=$(date +%s); TOTAL=${TOTAL:-1665}; STEP=100
mkdir -p out/${OUT:-nd}
for ((a=0; a<TOTAL; a+=STEP)); do
  b=$((a+STEP-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  [ -f out/${OUT:-nd}/chunk_$a.done ] && continue
  if [ $(( $(date +%s) - START )) -gt ${BUDGET:-6600} ]; then echo "time budget used, stopping before chunk $a"; exit 0; fi
  t0=$(date +%s)
  rm -rf out/${OUT:-nd}/c_$a
  npx remotion render src/index.ts ${COMP:-NoDieShort} out/${OUT:-nd}/c_$a --sequence --image-format=jpeg --jpeg-quality=95 \
    --frames=$a-$b --gl=swangle --browser-executable=/opt/pw-browsers/chromium --concurrency=2 --timeout=300000 --log=error \
    > out/${OUT:-nd}/log_$a.txt 2>&1 && touch out/${OUT:-nd}/chunk_$a.done
  echo "chunk $a-$b: $(( $(date +%s) - t0 )) s, $(ls out/${OUT:-nd}/c_$a 2>/dev/null | wc -l) frames, done=$([ -f out/${OUT:-nd}/chunk_$a.done ] && echo yes || echo NO)"
done
echo "ALL CHUNKS DONE: $(ls out/${OUT:-nd}/*.done | wc -l)"
