#!/bin/bash
# render the 1990-frame picture in parts (each under the 2 h task limit): bash scripts/render_all.sh "0 499" "500 999"
cd "$(dirname "$0")/.."
mkdir -p out/parts
for r in "$@"; do
  set -- $r
  [ -s out/parts/p_$1.mp4 ] && continue
  node scripts/render.mjs out/parts/p_$1.mp4 $1 $2 4 2>&1 | grep -E "done|rror" | tail -2
done
echo PARTS_DONE
