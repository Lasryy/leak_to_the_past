import test from 'node:test';
import assert from 'node:assert/strict';
import {
  WIDTH, HEIGHT, MAX_AMMO, chooseEnemy, normalized, directionName,
  hitbox, intersects, movement, shotDecision, getScreenPoint, ENEMIES
} from '../logic.mjs';

test('fixed design viewport and six enemy archetypes', () => {
  assert.equal(WIDTH, 1280);
  assert.equal(HEIGHT, 720);
  assert.deepEqual(Object.keys(ENEMIES), ['normal','green','yellow','blue','red','purple']);
});
test('diagonal speed is normalized', () => {
  const v = movement(new Set(['KeyZ','KeyD']));
  assert.ok(Math.abs(Math.hypot(v.x, v.y) - 1) < 1e-12);
});
test('AZERTY, QWERTY and arrow keys are supported', () => {
  for (const key of ['KeyZ','KeyW','ArrowUp']) assert.equal(movement(new Set([key])).y, -1);
  for (const key of ['KeyQ','KeyA','ArrowLeft']) assert.equal(movement(new Set([key])).x, -1);
  assert.deepEqual(normalized(0, 0), { x: 0, y: 0 });
});
test('eight compass directions and idle preservation', () => {
  assert.equal(directionName(-1, -1), 'north-west');
  assert.equal(directionName(1, 1), 'south-east');
  assert.equal(directionName(0, 0, 'east'), 'east');
});
test('enemy types unlock at exact match times', () => {
  assert.equal(chooseEnemy(0, () => .999), 'normal');
  assert.equal(chooseEnemy(29.99, () => .999), 'normal');
  assert.equal(chooseEnemy(30, () => .999), 'green');
  assert.equal(chooseEnemy(60, () => .999), 'yellow');
  assert.equal(chooseEnemy(90, () => .999), 'red');
  assert.equal(chooseEnemy(120, () => .999), 'purple');
});
test('blood reload costs exactly one heart, does not fire immediately', () => {
  assert.deepEqual(shotDecision(0, 2, false, false), {
    action: 'recharge', ammo: MAX_AMMO, hearts: 1, specialPending: true
  });
  assert.equal(shotDecision(0, 1, false, false).action, 'empty');
  assert.equal(shotDecision(0, 3, true, false).action, 'empty');
  const followup = shotDecision(MAX_AMMO, 1, false, true);
  assert.equal(followup.action, 'shoot');
  assert.equal(followup.special, true);
  assert.equal(followup.ammo, MAX_AMMO - 1);
});
test('collision boxes remain centered with inflate offsets', () => {
  const player = hitbox({x: 0,y:0,size:128}, 60);
  const enemy = hitbox({x: 37,y:0,size:64}, 40);
  assert.equal(intersects(player, enemy), true);
  enemy.x = 46;
  assert.equal(intersects(player, enemy), false);
});
test('client coordinates account for CSS canvas scaling', () => {
  const canvas = {getBoundingClientRect: () => ({left:100,top:40,width:640,height:360})};
  assert.deepEqual(getScreenPoint(canvas, 420, 220), {x:640,y:360});
});
