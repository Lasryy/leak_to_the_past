// Browser audio: decoded/cacheable effects through WebAudio, HTMLAudio fallback.
// Music uses one persistent HTMLAudio instance and starts only after user gesture.
const sounds = {
  shoot: ['nasal_spray.ogg', 'nasal_spray 2.ogg', 'nasal_spray 3.ogg'],
  empty: ['nasal_spray empty.ogg', 'nasal_spray empty 2.ogg', 'nasal_spray empty 3.ogg'],
  blue: ['blue shoot.ogg', 'blue shoot 2.ogg', 'blue shoot 3.ogg'],
  recharge: ['recharge.ogg', 'recharge 2.ogg', 'recharge 3.ogg'],
  spawn: ['snot spawn.ogg', 'snot spawn 2.ogg', 'snot spawn 3.ogg'],
  blood: ['blood_shoot.ogg', 'blood_shoot 2.ogg', 'blood_shoot 3.ogg', 'blood_shoot 4.ogg'],
  puddle: ['flaque.ogg', 'flaque 2.ogg', 'flaque 3.ogg']
};
const url = filename => './assets/audio/' + filename;
const pick = values => values[Math.floor(Math.random() * values.length)];
const cap = value => Math.min(1, Math.max(0, value));

export class Sound {
  constructor() {
    this.master = .8;
    this.muted = false;
    this.unlocked = false;
    this.paused = false;
    this.music = null;
    this.tracks = [1, 2, 3, 4, 5, 6].sort(() => Math.random() - .5);
    this.context = null;
    this.buffers = new Map();
    this.channels = new Map();
    this.voices = new Set();
    this.onChange = null;
    this.preloadStarted = false;
    this.missing = new Set();
  }
  preload() {
    if (this.preloadStarted) return;
    this.preloadStarted = true;
    const Context = window.AudioContext || window.webkitAudioContext;
    if (!Context) return; // Fall back to native HTMLAudio below.
    try { this.context = new Context(); }
    catch (error) { console.warn('WebAudio unavailable, fallback active:', error); return; }
    // Load once and decode in advance. No autoplay is attempted here.
    for (const name of Object.values(sounds).flat()) {
      fetch(url(name)).then(response => {
        if (!response.ok) throw new Error(response.status + ' ' + name);
        return response.arrayBuffer();
      }).then(bytes => this.context.decodeAudioData(bytes))
        .then(buffer => this.buffers.set(name, buffer))
        .catch(error => {
          if (!this.missing.has(name)) console.warn('Sound decode unavailable:', name, error);
          this.missing.add(name);
        });
    }
  }
  unlock() {
    this.preload();
    this.unlocked = true;
    this.context?.resume().catch(() => {});
    if (!this.music) {
      this.music = new Audio(url('track_' + this.tracks[0] + '.ogg'));
      this.music.loop = true;
      this.music.preload = 'auto';
      this.music.addEventListener('error', () =>
        console.warn('Music could not be loaded in this browser.'));
    }
    this.syncMusic();
  }
  syncMusic() {
    if (!this.music) return;
    this.music.volume = this.muted ? 0 : this.master * .5;
    if (this.paused) {
      this.music.pause();
    } else if (this.unlocked) {
      this.music.play().catch(error => {
        if (error?.name !== 'NotAllowedError' && error?.name !== 'AbortError')
          console.warn('Music playback unavailable:', error);
      });
    }
  }
  play(group, channel = '') {
    if (!this.unlocked || this.paused || this.muted || this.master === 0) return;
    // Limit simultaneous voices so rapid kills cannot turn into loud clipping.
    if (this.voices.size >= 24) return;
    const name = pick(sounds[group]);
    if (!name) return;
    const prev = channel ? this.channels.get(channel) : null;
    if (prev) {
      if (channel === 'empty' || channel === 'puddle') return;
      prev.stop();
    }
    if (this.context && this.context.state === 'running' && this.buffers.has(name)) {
      const source = this.context.createBufferSource();
      const gain = this.context.createGain();
      source.buffer = this.buffers.get(name);
      gain.gain.value = this.master * .7;
      source.connect(gain).connect(this.context.destination);
      const voice = { stop: () => { try { source.stop(); } catch {} }, gain };
      this.voices.add(voice);
      if (channel) this.channels.set(channel, voice);
      source.addEventListener('ended', () => this.forget(voice, channel), { once: true });
      source.start();
      return;
    }
    // Until WebAudio has decoded the sample, use a real browser audio element.
    const html = new Audio(url(name));
    html.preload = 'auto';
    html.volume = this.master * .7;
    const voice = { stop: () => { html.pause(); html.currentTime = 0; }, html };
    this.voices.add(voice);
    if (channel) this.channels.set(channel, voice);
    const cleanup = () => this.forget(voice, channel);
    html.addEventListener('ended', cleanup, { once: true });
    html.addEventListener('error', cleanup, { once: true });
    html.play().catch(cleanup);
  }
  forget(voice, channel) {
    this.voices.delete(voice);
    if (channel && this.channels.get(channel) === voice)
      this.channels.delete(channel);
  }
  stopChannel(channel) {
    const voice = this.channels.get(channel);
    if (voice) { voice.stop(); this.forget(voice, channel); }
  }
  stopAll() {
    for (const voice of this.voices) voice.stop();
    this.voices.clear();
    this.channels.clear();
  }
  pause() {
    this.paused = true;
    this.stopAll();
    this.syncMusic();
  }
  resume() {
    this.paused = false;
    this.unlock();
  }
  volume(delta) { this.setMaster(this.master + delta); }
  setMaster(next) {
    this.master = Math.round(cap(next) * 100) / 100;
    this.updateLevels();
  }
  toggleMute() {
    this.muted = !this.muted;
    if (this.muted) this.stopAll();
    this.updateLevels();
  }
  updateLevels() {
    for (const voice of this.voices) {
      if (voice.gain) voice.gain.gain.value = this.muted ? 0 : this.master * .7;
      if (voice.html) voice.html.volume = this.muted ? 0 : this.master * .7;
    }
    this.syncMusic();
    this.onChange?.();
  }
}
