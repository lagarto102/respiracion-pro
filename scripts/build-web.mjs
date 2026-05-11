import { cp, mkdir, rm } from 'node:fs/promises';
import path from 'node:path';

const root = process.cwd();
const outDir = path.join(root, 'www');
const files = ['index.html', 'privacy.html', 'manifest.json', 'sw.js'];
const dirs = ['icons'];

await mkdir(outDir, { recursive: true });

async function removeGenerated(target) {
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      await rm(target, { recursive: true, force: true });
      return;
    } catch (error) {
      if (error.code !== 'EBUSY' || attempt === 3) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
}

for (const file of files) {
  await removeGenerated(path.join(outDir, file));
}

for (const dir of dirs) {
  await removeGenerated(path.join(outDir, dir));
}

for (const file of files) {
  await cp(path.join(root, file), path.join(outDir, file));
}

for (const dir of dirs) {
  await cp(path.join(root, dir), path.join(outDir, dir), { recursive: true });
}

console.log(`Built web assets in ${outDir}`);
