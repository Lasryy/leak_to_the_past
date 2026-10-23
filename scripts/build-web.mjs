import { cpSync, copyFileSync, existsSync, mkdirSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = resolve(root, 'dist');
const source = resolve(root, 'web');
const assets = resolve(root, 'assets');
const required = [
  'graphics/spritesheet/leak.png', 'graphics/spritesheet/snot.png',
  'graphics/HUD/title_screen.png', 'graphics/HUD/game_over_screen.png',
  'graphics/HUD/heart.png', 'graphics/HUD/nasal_spray.png',
  'font/Monocraft.ttf',
  ...Array.from({length: 6}, (_, i) => 'audio/track_' + (i+1) + '.ogg'),
  'audio/nasal_spray.ogg', 'audio/nasal_spray 2.ogg', 'audio/nasal_spray 3.ogg',
  'audio/nasal_spray empty.ogg', 'audio/nasal_spray empty 2.ogg',
  'audio/nasal_spray empty 3.ogg',
  'audio/blue shoot.ogg', 'audio/blue shoot 2.ogg', 'audio/blue shoot 3.ogg',
  'audio/recharge.ogg', 'audio/recharge 2.ogg', 'audio/recharge 3.ogg',
  'audio/snot spawn.ogg', 'audio/snot spawn 2.ogg', 'audio/snot spawn 3.ogg',
  'audio/blood_shoot.ogg', 'audio/blood_shoot 2.ogg',
  'audio/blood_shoot 3.ogg', 'audio/blood_shoot 4.ogg',
  'audio/flaque.ogg', 'audio/flaque 2.ogg', 'audio/flaque 3.ogg'
];
for (const relative of required) {
  if (!existsSync(join(assets, relative)))
    throw new Error('Missing source asset: ' + relative);
}
if (!existsSync(source)) throw new Error('Missing web source folder');
// Only generated output is cleared. Original Python code is never deleted.
rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });
for (const name of ['index.html', 'style.css', 'logic.mjs', 'game.mjs', 'audio.mjs'])
  copyFileSync(join(source, name), join(out, name));
copyFileSync(join(root, 'favicon.png'), join(out, 'favicon.png'));
for (const folder of ['graphics', 'audio']) {
  cpSync(join(assets, folder), join(out, 'assets', folder), { recursive: true });
}
mkdirSync(join(out, 'assets', 'font'), { recursive: true });
copyFileSync(join(assets, 'font', 'Monocraft.ttf'),
  join(out, 'assets', 'font', 'Monocraft.ttf'));
writeFileSync(join(out, '.nojekyll'), '');
let count = 0, bytes = 0;
function walk(folder) {
  for (const item of readdirSync(folder)) {
    const path = join(folder, item);
    if (statSync(path).isDirectory()) walk(path);
    else { count++; bytes += statSync(path).size; }
  }
}
walk(out);
console.log('Web build ready: ' + count + ' files, ' + (bytes/1048576).toFixed(2) + ' MiB');
