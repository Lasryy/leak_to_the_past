// Pure gameplay helpers. Keep independent of browser APIs for regression tests.
export const WIDTH = 1280;
export const HEIGHT = 720;
export const TILE = 128;
export const MAX_AMMO = 30;
export const DROP_CHANCE = 0.15;
export const DIRECTIONS = [
  'south', 'south-west', 'west', 'north-west',
  'north', 'north-east', 'east', 'south-east'
];
export const ENEMIES = Object.freeze({
  normal: { speed: 150, health: 1, size: 64, color: null, score: 10 },
  green:  { speed: 250, health: 1, size: 64, color: [100, 255, 100], score: 15 },
  yellow: { speed: 200, health: 2, size: 128, color: [255, 255, 100], score: 25 },
  blue:   { speed: 180, health: 2, size: 64, color: [50, 50, 255], score: 10 },
  red:    { speed: 100, health: 10, size: 64, color: [255, 50, 50], score: 50 },
  purple: { speed: 350, health: 2, size: 64, color: [200, 50, 200], score: 100 }
});
export const SPAWNS = [
  { type: 'normal', weight: 60, after: 0 },
  { type: 'green', weight: 15, after: 30 },
  { type: 'yellow', weight: 15, after: 60 },
  { type: 'blue', weight: 5, after: 90 },
  { type: 'red', weight: 2, after: 90 },
  { type: 'purple', weight: 1, after: 120 }
];
export const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
export const rand = (lo, hi) => lo + Math.random() * (hi - lo);
export const randint = (lo, hi) => Math.floor(rand(lo, hi + 1));
export const pick = list => list[Math.floor(Math.random() * list.length)];
export const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
export function normalized(x, y, fallback = { x: 0, y: 0 }) {
  const length = Math.hypot(x, y);
  return length ? { x: x / length, y: y / length } : { ...fallback };
}
export function directionName(x, y, previous = 'south') {
  if (!x && !y) return previous;
  if (y < -0.4 && Math.abs(x) < 0.4) return 'north';
  if (y > 0.4 && Math.abs(x) < 0.4) return 'south';
  if (x > 0.4 && Math.abs(y) < 0.4) return 'east';
  if (x < -0.4 && Math.abs(y) < 0.4) return 'west';
  return (y < 0 ? 'north' : 'south') + '-' + (x > 0 ? 'east' : 'west');
}
export function chooseEnemy(elapsedSeconds, random = Math.random) {
  const available = SPAWNS.filter(s => elapsedSeconds >= s.after);
  const sum = available.reduce((total, s) => total + s.weight, 0);
  let value = random() * sum;
  for (const candidate of available) {
    value -= candidate.weight;
    if (value < 0) return candidate.type;
  }
  return available[available.length - 1].type;
}
// Rect geometry mirrors Pygame's rect.inflate hitboxes (centered, axis aligned).
export const hitbox = (entity, shrinkX = 0, shrinkY = shrinkX) => ({
  x: entity.x, y: entity.y,
  w: Math.max(0, entity.size - shrinkX),
  h: Math.max(0, entity.size - shrinkY)
});
export function intersects(a, b) {
  return Math.abs(a.x - b.x) * 2 < a.w + b.w
    && Math.abs(a.y - b.y) * 2 < a.h + b.h;
}
export function movement(keys) {
  const y = keys.has('KeyZ') || keys.has('KeyW') || keys.has('ArrowUp') ? -1
    : keys.has('KeyS') || keys.has('ArrowDown') ? 1 : 0;
  const x = keys.has('KeyQ') || keys.has('KeyA') || keys.has('ArrowLeft') ? -1
    : keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0;
  return normalized(x, y);
}
export function shotDecision(ammo, hearts, sprayPresent, specialPending) {
  if (ammo <= 0) {
    if (hearts > 1 && !sprayPresent)
      return { action: 'recharge', ammo: MAX_AMMO, hearts: hearts - 1, specialPending: true };
    return { action: 'empty', ammo, hearts, specialPending: false };
  }
  return {
    action: 'shoot', ammo: ammo - 1, hearts,
    special: Boolean(specialPending), specialPending: false
  };
}
export function getScreenPoint(canvas, clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  return { x: (clientX - rect.left) * WIDTH / rect.width,
           y: (clientY - rect.top) * HEIGHT / rect.height };
}
