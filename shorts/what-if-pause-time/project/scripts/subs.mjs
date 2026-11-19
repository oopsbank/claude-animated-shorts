// Renders the transparent subtitle layer (ProRes 4444 + alpha) and burns it over the finished film.
// usage: node scripts/subs.mjs   -> out/subs.mov, then ffmpeg -> ../final/windscreen_final_subs.mp4
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "node:path";
import { execFileSync } from "node:child_process";
const browserExecutable = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: "PauseSubs", browserExecutable });
await renderMedia({ composition, serveUrl, browserExecutable, codec: "prores", proResProfile: "4444", imageFormat: "png",
  pixelFormat: "yuva444p10le", outputLocation: "out/subs.mov", muted: true, concurrency: 4 });
execFileSync("ffmpeg", ["-v", "error", "-y", "-i", "out/windscreen_final.mp4", "-i", "out/subs.mov",
  "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]", "-map", "[v]", "-map", "0:a", "-c:v", "libx264",
  "-preset", "slow", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", "../final/windscreen_final_subs.mp4"], { stdio: "inherit" });
console.log("done");
