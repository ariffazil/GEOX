import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const guiRoot = resolve(here, '..');
const source = resolve(guiRoot, 'node_modules/cesium/Build/Cesium');
const destination = resolve(guiRoot, '../static/gui/cesium');

if (!existsSync(source)) {
  throw new Error(`Cesium runtime not installed at ${source}`);
}

mkdirSync(destination, { recursive: true });
cpSync(source, destination, { recursive: true, force: true });
console.log(`[geox-gui] Cesium runtime copied lazily to ${destination}`);
