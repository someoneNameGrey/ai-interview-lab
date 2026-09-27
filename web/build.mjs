import { build } from "esbuild";
import { readdir, unlink, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const outdir = fileURLToPath(new URL("../grey_interview/static/assets/", import.meta.url));
await mkdir(outdir, { recursive: true });
// This directory contains generated browser assets only. Remove stale chunks on rebuild.
for (const file of await readdir(outdir, { withFileTypes: true })) {
  if (file.isFile() && /\.(js|css|txt)$/.test(file.name)) await unlink(join(outdir, file.name));
}
await build({
  entryPoints: [fileURLToPath(new URL("app.js", import.meta.url))],
  bundle: true, splitting: true, format: "esm", minify: true, outdir,
  entryNames: "app", chunkNames: "chunk-[hash]", legalComments: "linked", logLevel: "info",
});
