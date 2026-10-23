import {
  WIDTH, HEIGHT, TILE, MAX_AMMO, DROP_CHANCE, DIRECTIONS, ENEMIES,
  clamp, rand, randint, pick, distance, normalized, directionName,
  chooseEnemy, hitbox, intersects, movement, shotDecision, getScreenPoint
} from './logic.mjs';

const imagePaths = {
  player: 'graphics/spritesheet/leak.png',
  enemy: 'graphics/spritesheet/snot.png',
  heart: 'graphics/HUD/heart.png',
  spray: 'graphics/HUD/nasal_spray.png',
  menu: 'graphics/HUD/title_screen.png',
  gameOver: 'graphics/HUD/game_over_screen.png'
};
const soundPaths = {
  shoot: ['nasal_spray.ogg', 'nasal_spray 2.ogg', 'nasal_spray 3.ogg'],
  empty: ['nasal_spray empty.ogg', 'nasal_spray empty 2.ogg', 'nasal_spray empty 3.ogg'],
  blue: ['blue shoot.ogg', 'blue shoot 2.ogg', 'blue shoot 3.ogg'],
  recharge: ['recharge.ogg', 'recharge 2.ogg', 'recharge 3.ogg'],
  spawn: ['snot spawn.ogg', 'snot spawn 2.ogg', 'snot spawn 3.ogg'],
  blood: ['blood_shoot.ogg', 'blood_shoot 2.ogg', 'blood_shoot 3.ogg', 'blood_shoot 4.ogg'],
  puddle: ['flaque.ogg', 'flaque 2.ogg', 'flaque 3.ogg']
};
const asset = path => './assets/' + path;
function createCanvas(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return canvas;
}
function loadImage(path) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Image introuvable : ' + path));
    image.src = path;
  });
}
function paintImage(image, width, height, angle = 0) {
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  ctx.translate(width / 2, height / 2);
  ctx.rotate(angle);
  ctx.drawImage(image, -20, -20, 40, 40);
  return canvas;
}
function cropFrame(sheet, col, row, size, tint) {
  const width = sheet.width / 7;
  const height = sheet.height / 8;
  const frame = createCanvas(size, size);
  const ctx = frame.getContext('2d', { willReadFrequently: true });
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(sheet, col * width, row * height, width, height, 0, 0, size, size);
  if (tint) {
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = 'rgb(' + tint.join(',') + ')';
    ctx.fillRect(0, 0, size, size);
    ctx.globalCompositeOperation = 'destination-in';
    ctx.drawImage(sheet, col * width, row * height, width, height, 0, 0, size, size);
    ctx.globalCompositeOperation = 'source-over';
  }
  return frame;
}
function makeFrames(sheet, size, tint) {
  const idle = {}, walk = {};
  for (let row = 0; row < DIRECTIONS.length; row++) {
    const name = DIRECTIONS[row];
    idle[name] = cropFrame(sheet, 0, row, size, tint);
    walk[name] = [];
    for (let col = 1; col <= 6; col++) walk[name].push(cropFrame(sheet, col, row, size, tint));
  }
  return { idle, walk };
}
function drawCentered(ctx, image, x, y, alpha = 1) {
  if (!image) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.drawImage(image, Math.round(x - image.width / 2), Math.round(y - image.height / 2));
  ctx.restore();
}
class Sound {
  constructor() {
    this.master = 1;
    this.music = null;
    this.live = new Set();
    this.channels = {};
    this.unlocked = false;
    this.tracks = [1, 2, 3, 4, 5, 6].sort(() => Math.random() - .5);
  }
  unlock() {
    if (this.unlocked) return;
    this.unlocked = true;
    const track = this.tracks[0];
    this.music = new Audio(asset('audio/track_' + track + '.ogg'));
    this.music.loop = true;
    this.music.preload = 'auto';
    this.music.volume = this.master * .5;
    this.music.play().catch(() => {});
  }
  play(group, channel = '') {
    if (!this.unlocked) return;
    if (channel && this.channels[channel] && !this.channels[channel].paused) {
      if (channel === 'empty' || channel === 'puddle') return;
      this.channels[channel].pause();
      this.channels[channel].currentTime = 0;
    }
    const audio = new Audio(asset('audio/' + pick(soundPaths[group])));
    audio.volume = this.master * .7;
    this.live.add(audio);
    if (channel) this.channels[channel] = audio;
    const remove = () => {
      this.live.delete(audio);
      if (channel && this.channels[channel] === audio) delete this.channels[channel];
    };
    audio.addEventListener('ended', remove, { once: true });
    audio.addEventListener('error', remove, { once: true });
    audio.play().catch(remove);
  }
  stopChannel(channel) {
    const audio = this.channels[channel];
    if (audio) {
      audio.pause();
      this.live.delete(audio);
      delete this.channels[channel];
    }
  }
  volume(delta) {
    this.master = clamp(Math.round((this.master + delta) * 10) / 10, 0, 1);
    if (this.music) this.music.volume = this.master * .5;
    for (const audio of this.live) audio.volume = this.master * .7;
  }
}
class Game {
  constructor(canvas, images) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d', { alpha: false });
    this.ctx.imageSmoothingEnabled = false;
    this.images = images;
    this.playerFrames = makeFrames(images.player, 128, null);
    this.enemyFrames = new Map();
    for (const [type, config] of Object.entries(ENEMIES)) {
      this.enemyFrames.set(type, makeFrames(images.enemy, config.size, config.color));
    }
    // Cache the original game's fixed, player-centred flashlight.
    this.fog = createCanvas(WIDTH, HEIGHT);
    const fogctx = this.fog.getContext('2d');
    fogctx.fillStyle = 'rgba(20,20,35,0.98)';
    fogctx.fillRect(0, 0, WIDTH, HEIGHT);
    fogctx.globalCompositeOperation = 'destination-out';
    const gradient = fogctx.createRadialGradient(WIDTH/2, HEIGHT/2, 0, WIDTH/2, HEIGHT/2, 450);
    gradient.addColorStop(0, 'rgba(0,0,0,1)');
    gradient.addColorStop(.75, 'rgba(0,0,0,.55)');
    gradient.addColorStop(1, 'rgba(0,0,0,0)');
    fogctx.fillStyle = gradient;
    fogctx.fillRect(0, 0, WIDTH, HEIGHT);
    fogctx.globalCompositeOperation = 'source-over';
    this.spray = paintImage(images.spray, 64, 64, Math.PI / 4);
    this.heart = images.heart;
    this.sound = new Sound();
    this.keys = new Set();
    this.state = 'menu';
    this.playedAt = 0;
    this.nextSpawnAt = 0;
    this.volumeDisplayUntil = 0;
    this.hintUntil = 0;
    this.clock = performance.now();
    this.createWorld();
    this.installInputs();
  }
  createWorld() {
    this.player = {
      x: WIDTH / 2, y: HEIGHT / 2, size: 128, dir: 'south',
      moving: false, speed: 500, baseSpeed: 500,
      frame: 0, ammo: MAX_AMMO, special: false
    };
    this.enemies = [];
    this.bullets = [];
    this.enemyBullets = [];
    this.particles = [];
    this.puddles = [];
    this.items = [];
    this.hearts = 1;
    this.score = 0;
    this.scoreCached = -1;
  }
  startGame(now = performance.now()) {
    this.createWorld();
    this.playedAt = now;
    this.nextSpawnAt = now + 1000;
    this.state = 'game';
  }
  installInputs() {
    window.addEventListener('keydown', event => {
      if (['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(event.code))
        event.preventDefault();
      this.keys.add(event.code);
      if (event.repeat) return;
      this.sound.unlock();
      if (!this.hintUntil) this.hintUntil = performance.now() + 5000;
      if (event.code === 'Equal' || event.code === 'NumpadAdd' || event.key === '+') {
        this.sound.volume(.1);
        this.volumeDisplayUntil = performance.now() + 2000;
      } else if (event.code === 'Minus' || event.code === 'NumpadSubtract' || event.key === '-') {
        this.sound.volume(-.1);
        this.volumeDisplayUntil = performance.now() + 2000;
      } else if (event.code === 'Space' && this.state !== 'game') {
        this.startGame();
      }
    });
    window.addEventListener('keyup', event => this.keys.delete(event.code));
    window.addEventListener('blur', () => this.keys.clear());
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) this.keys.clear();
      this.clock = performance.now();
    });
    this.canvas.addEventListener('contextmenu', event => event.preventDefault());
    this.canvas.addEventListener('pointerdown', event => {
      if (event.button !== 0) return;
      this.canvas.focus({ preventScroll: true });
      this.sound.unlock();
      if (!this.hintUntil) this.hintUntil = performance.now() + 5000;
      if (this.state === 'game' && !this.player.moving) {
        const target = getScreenPoint(this.canvas, event.clientX, event.clientY);
        this.shoot(target);
      }
    });
  }
  spawnEnemy(now, type = null, position = null) {
    const elapsed = (now - this.playedAt) / 1000;
    type ??= chooseEnemy(elapsed);
    const angle = randint(0, 360) * Math.PI / 180;
    const distanceFromPlayer = randint(1000, 1200);
    const pos = position || {
      x: this.player.x + Math.cos(angle) * distanceFromPlayer,
      y: this.player.y + Math.sin(angle) * distanceFromPlayer
    };
    const cfg = ENEMIES[type];
    this.enemies.push({
      x: pos.x, y: pos.y, size: cfg.size, type,
      health: cfg.health, speed: cfg.speed, dir: 'south', frame: 0,
      hitUntil: 0, shotAt: now, tpAt: now, zigzagAt: 0, zigzagSign: 1
    });
    if (type === 'blue') this.sound.play('spawn');
  }
  shoot(target) {
    const player = this.player;
    const decision = shotDecision(player.ammo, this.hearts,
      this.items.length > 0, player.special);
    player.ammo = decision.ammo;
    player.special = decision.specialPending;
    this.hearts = decision.hearts;
    if (decision.action === 'empty') {
      this.sound.play('empty', 'empty');
      return;
    }
    if (decision.action === 'recharge') {
      this.sound.play('recharge');
      return;
    }
    this.sound.play('shoot', 'shoot');
    if (decision.special) this.sound.play('blood');
    const heading = normalized(target.x - WIDTH/2, target.y - HEIGHT/2, { x: 0, y: -1 });
    player.dir = directionName(heading.x, heading.y, player.dir);
    this.bullets.push({
      x: player.x, y: player.y, dir: heading, special: decision.special,
      born: performance.now(), speed: 800, lifetime: 1000
    });
  }
  updatePlayer(dt) {
    const player = this.player;
    const dir = movement(this.keys);
    player.moving = Boolean(dir.x || dir.y);
    if (player.moving) {
      player.dir = directionName(dir.x, dir.y, player.dir);
      player.frame = (player.frame + 12 * dt) % 6;
    } else {
      player.frame = 0;
    }
    player.x += dir.x * player.speed * dt;
    player.y += dir.y * player.speed * dt;
  }
  updateEnemies(dt, now) {
    const player = this.player;
    for (const enemy of this.enemies) {
      let dir = normalized(player.x - enemy.x, player.y - enemy.y);
      // Local separation, mirroring Pygame's 10px inflated scan rect.
      let sx = 0, sy = 0;
      for (const other of this.enemies) {
        if (enemy === other) continue;
        if (Math.abs(enemy.x - other.x) >= (enemy.size + other.size)/2 + 10
          || Math.abs(enemy.y - other.y) >= (enemy.size + other.size)/2 + 10) continue;
        const vx = enemy.x - other.x, vy = enemy.y - other.y;
        const length = Math.hypot(vx, vy);
        if (length > 0 && length < enemy.size) {
          sx += vx / (length * length);
          sy += vy / (length * length);
        }
      }
      dir = normalized(dir.x + sx * 1.5, dir.y + sy * 1.5);
      if (enemy.type === 'blue') {
        const dist = distance(enemy, player);
        if (dist < 250) dir = { x: -dir.x, y: -dir.y };
        else if (dist < 350) dir = { x: 0, y: 0 };
        if (now - enemy.shotAt > 2000) {
          enemy.shotAt = now;
          this.blueShoot(enemy, now);
        }
      }
      if (enemy.type === 'purple') {
        enemy.zigzagAt += dt;
        if (enemy.zigzagAt > .2) {
          enemy.zigzagAt = 0;
          enemy.zigzagSign *= -1;
        }
        dir = normalized(dir.x + (-dir.y * enemy.zigzagSign * .5),
          dir.y + (dir.x * enemy.zigzagSign * .5));
      }
      enemy.dir = directionName(dir.x, dir.y, enemy.dir);
      enemy.frame = (enemy.frame + (enemy.speed / 25) * dt) % 6;
      enemy.x += dir.x * enemy.speed * dt;
      enemy.y += dir.y * enemy.speed * dt;
      if (enemy.type === 'purple' && now - enemy.tpAt >= 800) {
        let closest = null, min = Infinity;
        for (const other of this.enemies) {
          if (other === enemy) continue;
          const d = distance(other, player);
          if (d < min) { min = d; closest = other; }
        }
        if (closest) {
          const back = normalized(closest.x - player.x, closest.y - player.y);
          if (back.x || back.y) {
            enemy.x = closest.x + back.x * 50;
            enemy.y = closest.y + back.y * 50;
            enemy.tpAt = now;
          }
        }
      }
    }
  }
  blueShoot(enemy, now) {
    const player = this.player;
    if (Math.abs(player.x - enemy.x) > WIDTH/2 + 100
      || Math.abs(player.y - enemy.y) > HEIGHT/2 + 100) return;
    this.enemyBullets.push({
      x: enemy.x, y: enemy.y,
      dir: normalized(player.x - enemy.x, player.y - enemy.y, { x: 1, y: 0 }),
      born: now, speed: 300, lifetime: 3000, size: 12
    });
    this.sound.play('blue');
  }
  killEnemy(enemy, special, now) {
    const cfg = ENEMIES[enemy.type];
    for (let i = 0; i < 8; i++) {
      this.particles.push({
        x: enemy.x, y: enemy.y,
        dir: normalized(rand(-1, 1), rand(-1, 1)),
        speed: rand(100, 300), born: now, lifetime: rand(200, 500),
        color: cfg.color || [255, 255, 255]
      });
    }
    this.score += cfg.score;
    if (enemy.type === 'red') this.hearts = Math.min(3, this.hearts + 1);
    if (enemy.type === 'yellow' && !special) {
      for (let i = 0; i < 2; i++) {
        this.spawnEnemy(now, 'green', {
          x: enemy.x + randint(-50, 50), y: enemy.y + randint(-50, 50)
        });
      }
    }
    if (enemy.type === 'green' || enemy.type === 'yellow') {
      const size = randint(40, 60);
      this.puddles.push({ x: enemy.x, y: enemy.y, size, born: now, lifetime: 5000 });
    }
    const drop = enemy.type === 'blue' || Math.random() < (this.items.length ? DROP_CHANCE/5 : DROP_CHANCE);
    if (drop) {
      this.items.push({ x: enemy.x, y: enemy.y, initialY: enemy.y, born: now,
        lifetime: 10000, float: 0, size: 56 });
    }
    this.enemies.splice(this.enemies.indexOf(enemy), 1);
  }
  // Match groupcollide: one shot can damage every enemy overlapping in that frame.
  collideShots(now) {
    const remaining = [];
    for (const bullet of this.bullets) {
      const angle = Math.atan2(bullet.dir.y, bullet.dir.x);
      const w = 24 * Math.abs(Math.cos(angle)) + 6 * Math.abs(Math.sin(angle));
      const h = 24 * Math.abs(Math.sin(angle)) + 6 * Math.abs(Math.cos(angle));
      const impacted = this.enemies.filter(enemy => intersects(
        { x: bullet.x, y: bullet.y, w, h },
        { x: enemy.x, y: enemy.y, w: enemy.size, h: enemy.size }
      ));
      if (!impacted.length) { remaining.push(bullet); continue; }
      for (const enemy of impacted) {
        if (!this.enemies.includes(enemy)) continue;
        enemy.health = bullet.special ? 0 : enemy.health - 1;
        enemy.hitUntil = now + 100;
        if (enemy.health <= 0) this.killEnemy(enemy, bullet.special, now);
      }
    }
    this.bullets = remaining;
  }
  frameForPlayer() {
    const p = this.player;
    return p.moving ? this.playerFrames.walk[p.dir][Math.floor(p.frame)]
      : this.playerFrames.idle[p.dir];
  }
  // Pygame's blue-bullet-vs-player collision uses collide_mask, not the
  // smaller movement hitbox. Sample the actual sprite alpha.
  hitsPlayerMask(bullet) {
    const frame = this.frameForPlayer();
    if (Math.abs(bullet.x - this.player.x) >= 70 || Math.abs(bullet.y - this.player.y) >= 70)
      return false;
    const ctx = frame.getContext('2d', { willReadFrequently: true });
    const data = ctx.getImageData(0, 0, 128, 128).data;
    const centerX = Math.round(this.player.x);
    const centerY = Math.round(this.player.y);
    for (let dy = -6; dy < 6; dy++) {
      for (let dx = -6; dx < 6; dx++) {
        const sx = Math.round(bullet.x) + dx - centerX + 64;
        const sy = Math.round(bullet.y) + dy - centerY + 64;
        if (sx >= 0 && sx < 128 && sy >= 0 && sy < 128 && data[(sy * 128 + sx) * 4 + 3] > 0)
          return true;
      }
    }
    return false;
  }
  update(dt, now) {
    this.updatePlayer(dt);
    this.updateEnemies(dt, now);
    for (const group of [this.bullets, this.enemyBullets, this.particles]) {
      for (const entity of group) {
        entity.x += entity.dir.x * entity.speed * dt;
        entity.y += entity.dir.y * entity.speed * dt;
      }
    }
    for (const item of this.items) {
      item.float += dt * 5;
      item.y = item.initialY + Math.sin(item.float) * 5;
    }
    this.bullets = this.bullets.filter(e => now - e.born <= e.lifetime);
    this.enemyBullets = this.enemyBullets.filter(e => now - e.born <= e.lifetime);
    this.particles = this.particles.filter(e => now - e.born <= e.lifetime);
    this.puddles = this.puddles.filter(e => now - e.born <= e.lifetime);
    this.items = this.items.filter(e => now - e.born <= e.lifetime);

    while (now >= this.nextSpawnAt) {
      this.spawnEnemy(now);
      this.nextSpawnAt += 1000;
    }
    this.collideShots(now);
    const playerBox = hitbox(this.player, 60);
    for (const enemy of this.enemies) {
      if (!intersects(playerBox, hitbox(enemy, enemy.type === 'purple' ? 50 : 40))) continue;
      this.hearts--;
      if (this.hearts <= 0) {
        this.state = 'game_over';
      } else {
        this.enemies.splice(this.enemies.indexOf(enemy), 1);
      }
      break;
    }
    const slowed = this.puddles.some(p => intersects(playerBox, hitbox(p, 10)));
    this.player.speed = slowed ? this.player.baseSpeed / 2 : this.player.baseSpeed;
    if (slowed) this.sound.play('puddle', 'puddle');
    else this.sound.stopChannel('puddle');
    // A cluster of bullets can cause only one heart of damage per frame.
    let hasHit = false;
    this.enemyBullets = this.enemyBullets.filter(b => {
      if (this.hitsPlayerMask(b)) {
        hasHit = true;
        return false;
      }
      return true;
    });
    if (hasHit) {
      this.hearts--;
      if (this.hearts <= 0) this.state = 'game_over';
    }
    this.items = this.items.filter(item => {
      // Rotated 40x40 spray occupies a 56x56 bounding rectangle.
      if (!intersects(playerBox, hitbox(item, 30))) return true;
      this.player.ammo = MAX_AMMO;
      this.sound.play('recharge');
      return false;
    });
    if (this.state === 'game_over') this.sound.stopChannel('puddle');
  }
  drawWorld(now) {
    const ctx = this.ctx, player = this.player;
    const ox = Math.round(player.x - WIDTH/2), oy = Math.round(player.y - HEIGHT/2);
    ctx.fillStyle = '#141414';
    ctx.fillRect(0, 0, WIDTH, HEIGHT);
    ctx.strokeStyle = '#282828';
    ctx.lineWidth = 1;
    const startCol = Math.floor(ox / TILE) - 1, startRow = Math.floor(oy / TILE) - 1;
    for (let row = startRow; row <= Math.floor((oy + HEIGHT) / TILE) + 1; row++) {
      for (let col = startCol; col <= Math.floor((ox + WIDTH) / TILE) + 1; col++) {
        ctx.strokeRect(col*TILE - ox + .5, row*TILE - oy + .5, TILE, TILE);
      }
    }
    for (const puddle of this.puddles) {
      ctx.fillStyle = 'rgba(0,255,0,.39)';
      ctx.beginPath();
      ctx.arc(puddle.x - ox, puddle.y - oy, puddle.size / 2, 0, Math.PI * 2);
      ctx.fill();
    }
    const drawables = [{ y: player.y, draw: () => drawCentered(ctx, this.frameForPlayer(), player.x-ox, player.y-oy) }];
    for (const enemy of this.enemies) {
      drawables.push({ y: enemy.y, draw: () => {
        const frames = this.enemyFrames.get(enemy.type);
        const image = frames.walk[enemy.dir][Math.floor(enemy.frame)];
        const alpha = enemy.type === 'purple' && distance(enemy, player) < 300 ? 30/255 : 1;
        drawCentered(ctx, image, enemy.x - ox, enemy.y - oy, alpha);
        if (enemy.hitUntil > now) {
          ctx.save();
          ctx.globalCompositeOperation = 'lighter';
          drawCentered(ctx, image, enemy.x - ox, enemy.y - oy, alpha);
          ctx.restore();
        }
      }});
    }
    for (const bullet of this.bullets) {
      drawables.push({ y: bullet.y, draw: () => {
        ctx.save();
        ctx.translate(Math.round(bullet.x - ox), Math.round(bullet.y - oy));
        ctx.rotate(Math.atan2(bullet.dir.y, bullet.dir.x));
        ctx.fillStyle = bullet.special ? '#ff0000' : '#00ffff';
        ctx.fillRect(-12, -3, 24, 6);
        ctx.restore();
      }});
    }
    for (const bullet of this.enemyBullets) {
      drawables.push({ y: bullet.y, draw: () => {
        const x = Math.round(bullet.x - ox), y = Math.round(bullet.y - oy);
        ctx.fillStyle = 'rgb(50,50,255)';
        ctx.fillRect(x-6, y-6, 12, 12);
        ctx.fillStyle = 'rgb(200,200,255)';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2*Math.PI);
        ctx.fill();
      }});
    }
    for (const particle of this.particles) {
      drawables.push({ y: particle.y, draw: () => {
        ctx.fillStyle = 'rgb(' + particle.color.join(',') + ')';
        ctx.fillRect(Math.round(particle.x-ox)-2, Math.round(particle.y-oy)-2, 4, 4);
      }});
    }
    for (const item of this.items) {
      drawables.push({ y: item.y, draw: () => {
        const age = now - item.born;
        const alpha = age > 8000 && (Math.floor(age / 200) % 2 === 0) ? 100/255 : 1;
        drawCentered(ctx, this.spray, item.x - ox, item.y - oy, alpha);
      }});
    }
    drawables.sort((a,b) => a.y - b.y);
    for (const drawable of drawables) drawable.draw();
    ctx.drawImage(this.fog, 0, 0);
  }
  text(message, x, y, size = 18, align = 'left', color = '#fff') {
    const ctx = this.ctx;
    ctx.font = size + 'px Monocraft, monospace';
    ctx.textBaseline = 'top';
    ctx.textAlign = align;
    ctx.fillStyle = 'rgba(0,0,0,.95)';
    ctx.fillText(message, x+1, y+1);
    ctx.fillStyle = color;
    ctx.fillText(message, x, y);
  }
  drawUI(now) {
    const ctx = this.ctx;
    const slotSize = 50, gap = 3, slots = 9;
    const barWidth = slots * (slotSize + gap) + gap;
    const barHeight = slotSize + gap * 2;
    const bx = WIDTH/2 - barWidth/2, by = HEIGHT - barHeight - 10;
    ctx.fillStyle = '#323232';
    ctx.fillRect(bx, by, barWidth, barHeight);
    ctx.strokeStyle = '#1e1e1e';
    ctx.lineWidth = 2;
    ctx.strokeRect(bx, by, barWidth, barHeight);
    for (let i=0; i<slots; i++) {
      const x = bx + gap + i * (slotSize + gap), y = by + gap;
      ctx.fillStyle = '#505050';
      ctx.fillRect(x, y, slotSize, slotSize);
      if (i) {
        ctx.strokeStyle = '#282828';
        ctx.lineWidth = 1;
        ctx.strokeRect(x + .5, y + .5, slotSize - 1, slotSize - 1);
      }
    }
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.strokeRect(bx+gap+1, by+gap+1, slotSize-2, slotSize-2);
    drawCentered(ctx, this.spray, bx + gap + 25, by + gap + 25);
    if (this.player.ammo < MAX_AMMO) {
      const ratio = this.player.ammo / MAX_AMMO;
      const x = bx + gap + 3, y = by + gap + slotSize - 8;
      ctx.fillStyle = '#000'; ctx.fillRect(x, y, slotSize-6, 4);
      ctx.fillStyle = ratio > .5 ? '#00ff00' : ratio > .2 ? '#ffa500' : '#ff0000';
      ctx.fillRect(x, y, (slotSize-6)*ratio, 4);
    }
    for (let i=0; i<this.hearts; i++) {
      ctx.drawImage(this.heart, bx+15+i*28-12, by-28-12, 24, 24);
    }
    this.text('Nasal Spray', WIDTH/2, by-25, 18, 'center');
    this.text('Score: ' + this.score, WIDTH-150, 20);
    if (now < this.volumeDisplayUntil)
      this.text('Volume: ' + Math.round(this.sound.master * 100) + '%', 20, 20);
    else if (now < this.hintUntil)
      this.text('Régler le volume avec + et -', 20, 20, 18, 'left', '#c8c8c8');
  }
  drawMenu() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    if (this.images.menu) ctx.drawImage(this.images.menu, 0, 0, WIDTH, HEIGHT);
    else this.text('LEAK TO THE PAST — ESPACE POUR JOUER', WIDTH/2, HEIGHT/2, 32, 'center');
  }
  drawGameOver() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, WIDTH, HEIGHT);
    if (this.images.gameOver) ctx.drawImage(this.images.gameOver, 0, 0, WIDTH, HEIGHT);
    else this.text('GAME OVER', WIDTH/2, HEIGHT/2 - 50, 40, 'center', 'red');
    this.text('Score: ' + this.score, WIDTH-150, 20);
  }
  render(now) {
    if (this.state === 'menu') return this.drawMenu();
    if (this.state === 'game_over') return this.drawGameOver();
    this.drawWorld(now);
    this.drawUI(now);
  }
  start() {
    const animate = now => {
      const dt = Math.min(Math.max((now - this.clock)/1000, 0), .1);
      this.clock = now;
      if (!document.hidden && this.state === 'game') this.update(dt, now);
      this.render(now);
      requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }
}
async function boot() {
  const loading = document.getElementById('loading');
  try {
    const images = {};
    const entries = Object.entries(imagePaths);
    await Promise.all(entries.map(async ([key, path]) => {
      images[key] = await loadImage(asset(path));
    }));
    if (document.fonts) await document.fonts.load('18px Monocraft');
    const canvas = document.getElementById('game');
    const game = new Game(canvas, images);
    loading.hidden = true;
    game.start();
  } catch (error) {
    console.error(error);
    loading.textContent = 'Impossible de charger le jeu : ' + error.message;
  }
}
boot();
