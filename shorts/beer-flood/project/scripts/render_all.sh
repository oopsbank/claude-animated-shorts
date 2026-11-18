#!/bin/bash
cd "$(dirname "$0")/.."
mkdir -p out/parts
for r in "0 499" "500 999" "1000 1499" "1500 1947"; do
  set -- $r
  [ -s out/parts/p_$1.mp4 ] && continue
  node scripts/render.mjs out/parts/p_$1.mp4 $1 $2 4 2>&1 | grep -E "frames|done|rror" | tail -3
done
echo ALL_DONE
