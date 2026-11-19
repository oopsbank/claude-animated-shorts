// usage: node scripts/render.mjs <out.mp4> [from] [to] [concurrency]
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [out, from, to, conc = "4"] = process.argv.slice(2);
const browserExecutable = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const chromiumOptions = { gl: "swangle" };
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: "PlaneShort", browserExecutable, chromiumOptions, timeoutInMilliseconds: 600000 });
const t0 = Date.now(); let last = 0;
await renderMedia({ composition, serveUrl, codec: "h264", crf: 16, outputLocation: out, browserExecutable, chromiumOptions,
  concurrency: Number(conc), timeoutInMilliseconds: 600000, muted: true,
  frameRange: from !== undefined ? [Number(from), Number(to)] : undefined,
  onProgress: ({ renderedFrames }) => { if (renderedFrames - last >= 25) { last = renderedFrames; console.log("frames", renderedFrames, ((Date.now() - t0) / 1000).toFixed(0) + "s"); } } });
console.log("done", ((Date.now() - t0) / 1000).toFixed(0) + "s");
