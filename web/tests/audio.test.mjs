import test from 'node:test';
import assert from 'node:assert/strict';
import { Sound } from '../audio.mjs';

test('Music and SFX levels are independent', () => {
  const mixer = new Sound();
  mixer.setMusicLevel(.2);
  mixer.setSfxLevel(.65);
  assert.equal(mixer.musicLevel, .2);
  assert.equal(mixer.sfxLevel, .65);
  assert.equal(mixer.effectiveMusicVolume(), mixer.master * .2);
  assert.equal(mixer.effectiveSfxVolume(), mixer.master * .65);
  mixer.setMusicLevel(0);
  assert.equal(mixer.effectiveMusicVolume(), 0);
  assert.ok(mixer.effectiveSfxVolume() > 0);
  mixer.setSfxLevel(0);
  mixer.setMusicLevel(.5);
  assert.equal(mixer.effectiveSfxVolume(), 0);
  assert.ok(mixer.effectiveMusicVolume() > 0);
});
test('Master and mute affect both streams without changing individual settings', () => {
  const mixer = new Sound();
  mixer.setMusicLevel(.3);
  mixer.setSfxLevel(.8);
  mixer.setMaster(.5);
  assert.equal(mixer.effectiveMusicVolume(), .15);
  assert.equal(mixer.effectiveSfxVolume(), .4);
  mixer.toggleMute();
  assert.equal(mixer.effectiveMusicVolume(), 0);
  assert.equal(mixer.effectiveSfxVolume(), 0);
  mixer.toggleMute();
  assert.equal(mixer.musicLevel, .3);
  assert.equal(mixer.sfxLevel, .8);
});
test('Every track is reachable, previous reverses next, wrapping works', () => {
  const mixer = new Sound();
  assert.equal(new Set(mixer.tracks).size, 6);
  assert.deepEqual([...mixer.tracks].sort((a, b) => a-b), [1,2,3,4,5,6]);
  const start = mixer.currentTrackNumber();
  const seen = new Set([start]);
  for (let i = 0; i < 5; i++) seen.add(mixer.nextTrack());
  assert.equal(seen.size, 6);
  assert.equal(mixer.nextTrack(), start);
  const previous = mixer.previousTrack();
  assert.notEqual(previous, start);
  assert.equal(mixer.nextTrack(), start);
});
test('Mixer clamps volume levels to 0–1', () => {
  const mixer = new Sound();
  mixer.setMaster(2);
  mixer.setMusicLevel(-10);
  mixer.setSfxLevel(.333);
  assert.equal(mixer.master, 1);
  assert.equal(mixer.musicLevel, 0);
  assert.equal(mixer.sfxLevel, .33);
});
