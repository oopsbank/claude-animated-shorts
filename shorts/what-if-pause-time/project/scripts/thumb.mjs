// Thumbnail background: one still of shot 1 with a custom camera and people (inputProps.thumb). usage: node scripts/thumb.mjs out.png frame
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [out, frame = "75", scale = "1"] = process.argv.slice(2);
const browserExecutable = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const chromiumOptions = { gl: "swangle" };
const thumb = JSON.parse(process.env.THUMB);
const inputProps = { thumb, ...(process.env.DPR ? { post: { dpr: Number(process.env.DPR) } } : {}) };
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: "PauseShort", browserExecutable, chromiumOptions, inputProps, timeoutInMilliseconds: 300000 });
await renderStill({ composition, serveUrl, frame: Number(frame), output: out, imageFormat: "png", scale: Number(scale), browserExecutable, chromiumOptions, inputProps, timeoutInMilliseconds: 300000 });
console.log("ok", out);
