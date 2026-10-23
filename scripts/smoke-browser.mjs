// Real Chromium smoke check for the published static build.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { join, resolve, extname, sep } from 'node:path';
import { chromium } from 'playwright';

const root = resolve('dist');
const contentTypes = {
  '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8',
  '.mjs':'text/javascript; charset=utf-8', '.png':'image/png',
  '.ogg':'audio/ogg', '.ttf':'font/ttf'
};
const server = createServer(async (req, res) => {
  let pathname = '/';
  try { pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname); }
  catch { res.writeHead(400).end(); return; }
  const candidate = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
  if (!candidate.startsWith(root + sep)) {
    res.writeHead(403).end();
    return;
  }
  try {
    const file = await readFile(candidate);
    res.setHeader('Content-Type', contentTypes[extname(candidate)] || 'application/octet-stream');
    res.writeHead(200).end(file);
  } catch {
    res.writeHead(404).end('Not found');
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const port = server.address().port;
let browser;
try {
  browser = await chromium.launch({channel: 'chrome', headless: true, args: ['--no-sandbox','--autoplay-policy=user-gesture-required']});
  const page = await browser.newPage({viewport:{width:1366,height:768}});
  const exceptions = [];
  const missing = [];
  page.on('pageerror', err => exceptions.push(err.message));
  page.on('response', response => {
    if (response.status() >= 400) missing.push(response.status() + ' ' + response.url());
  });
  await page.goto('http://127.0.0.1:' + port + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.getElementById('loading')?.hidden, {timeout:30000});
  await mkdir('browser-screenshots', {recursive:true});
  for (const [w,h] of [[1366,768],[1920,1080],[1280,720],[1024,600],[844,390],[390,844],[375,667]]) {
    await page.setViewportSize({width:w, height:h});
    const dims = await page.evaluate(() => {
      const frame = document.querySelector('.frame').getBoundingClientRect();
      const toolbar = document.querySelector('.controlbar').getBoundingClientRect();
      return {
        horizontal:document.documentElement.scrollWidth > innerWidth+1,
        vertical:document.documentElement.scrollHeight > innerHeight+1,
        frameTop:frame.top, frameBottom:frame.bottom, frameRight:frame.right,
        toolbarBottom:toolbar.bottom,
        viewWidth:innerWidth, viewHeight:innerHeight,
        frameWidth:frame.width, frameHeight:frame.height
      };
    });
    assert(!dims.horizontal && !dims.vertical, 'Unexpected page scroll at ' + w + 'x' + h + ': ' + JSON.stringify(dims));
    assert(dims.frameTop >= -1 && dims.frameBottom <= h + 1, 'Clipped game canvas at ' + w + 'x' + h);
    assert(dims.toolbarBottom <= h + 1, 'Clipped controls at ' + w + 'x' + h);
    assert(dims.frameWidth >= 150, 'Game viewport collapsed at ' + w + 'x' + h);
    if (w===1366 || w===390) {
      await page.screenshot({path:'browser-screenshots/' + w + 'x' + h + '.png', fullPage:true});
    }
  }
  await page.setViewportSize({width:1366,height:768});
  await page.keyboard.press('Space');
  await page.waitForTimeout(100);
  assert.equal(await page.locator('#pause-button').isEnabled(), true, 'Game did not enter playing state');
  await page.locator('#pause-button').click();
  assert.equal(await page.locator('#pause-overlay').isVisible(), true, 'Pause overlay missing');
  await page.locator('#resume-button').click();
  assert.equal(await page.locator('#pause-overlay').isVisible(), false, 'Resume control failed');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#pause-overlay').isVisible(), true, 'Escape did not pause');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#pause-overlay').isVisible(), false, 'Escape did not resume');
  const muteButton = page.locator('#sound-button');
  await muteButton.click();
  assert.equal(await muteButton.getAttribute('aria-pressed'), 'true', 'Mute failed');
  await muteButton.click();
  assert.equal(await muteButton.getAttribute('aria-pressed'), 'false', 'Unmute failed');
  await page.locator('#volume-control').fill('30');
  assert.equal(await page.locator('#volume-control').inputValue(), '30', 'Slider did not update volume');
  // Decode representative OGG assets in the real browser, not just HTTP-check them.
  const audioFormats = await page.evaluate(async () => {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    try {
      const result = [];
      for (const file of ['nasal_spray.ogg','blue shoot.ogg','track_1.ogg']) {
        const response = await fetch('./assets/audio/' + file);
        if (!response.ok) throw new Error('Audio fetch failed: ' + file);
        const buffer = await ctx.decodeAudioData(await response.arrayBuffer());
        result.push({file, duration:buffer.duration, channels:buffer.numberOfChannels});
      }
      return result;
    } finally {
      await ctx.close();
    }
  });
  for (const sound of audioFormats) {
    assert(sound.duration > 0 && sound.channels >= 1, 'Audio failed to decode: ' + sound.file);
  }

  // The browser should be able to make the game frame fullscreen, then restore it.
  await page.locator('#fullscreen-button').click();
  await page.waitForFunction(() => document.fullscreenElement !== null, {timeout:5000});
  assert.equal(await page.evaluate(() => document.fullscreenElement?.id), 'game-frame');
  await page.locator('#fullscreen-button').click();
  await page.waitForFunction(() => document.fullscreenElement === null, {timeout:5000});
  assert.equal(await page.evaluate(() => Boolean(document.fullscreenElement)), false);
  await page.screenshot({path:'browser-screenshots/gameplay.png', fullPage:true});
  assert.deepEqual(missing, [], 'Some static resources failed to load');
  assert.deepEqual(exceptions, [], 'JavaScript runtime exceptions');
  console.log('Browser UX smoke PASS: seven viewports, no scroll, pause, keyboard, mute/volume, OGG decoding, fullscreen.');
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
