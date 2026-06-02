import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const args = process.argv.slice(2);
const propsPath = valueAfter("--props");
const outputPath = valueAfter("--output");

if (!propsPath || !outputPath) {
  console.error("Usage: npm run render:factory -- --props /path/props.json --output /path/video.mp4");
  process.exit(2);
}

const here = dirname(fileURLToPath(import.meta.url));
const entry = resolve(here, "src/index.tsx");
const remotionBin = resolve(here, "../node_modules/.bin/remotion");
const props = JSON.parse(readFileSync(propsPath, "utf8"));
const output = resolve(outputPath);

mkdirSync(dirname(output), { recursive: true });

const result = spawnSync(
  remotionBin,
  [
    "render",
    entry,
    "FactoryVertical",
    output,
    "--props",
    JSON.stringify(props),
    "--overwrite"
  ],
  {
    cwd: resolve(here, ".."),
    stdio: "inherit"
  }
);

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

function valueAfter(name) {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : undefined;
}
