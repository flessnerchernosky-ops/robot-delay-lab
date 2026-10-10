/* Fixed-step, deterministic toy model. Also runs in Node for model checks. */
(function (root) {
  'use strict';
  const DT = 1 / 120, DRAG = 0.15, LIMIT = 6;
  const presets = {
    gentle: {delay:0, gain:3, damping:0.8, motion:'fixed',
      text:'先看没有延迟时，飞船如何停在星星附近。三艘飞船应完全同步。'},
    chaos: {delay:0.4, gain:4, damping:0.2, motion:'fixed',
      text:'新指令晚了 0.4 秒才生效。珊瑚色飞船会不会越纠正，越追过头？'},
    brake: {delay:0.4, gain:4, damping:0.7, motion:'fixed',
      text:'只增加刹车意愿，其他条件和上一关一样。晃动变小了吗？'},
    wander: {delay:0.6, gain:4, damping:0.7, motion:'wander',
      text:'星星开始转弯。紫色飞船只能猜它继续沿当前速度移动，并不知道下一次转弯。'},
    surprise: {delay:0.6, gain:1, damping:0.9, motion:'fast',
      text:'目标快速折返，保持当前速度的猜测很快失效。跑完 20 秒，看看预测是否反而更差。'}
  };
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  function targetAt(time, motion) {
    const rate = motion === 'fast' ? 3 : 0.65;
    return ['wander','fast'].includes(motion) ?
      {x:1.2*Math.cos(rate*time),v:-1.2*rate*Math.sin(rate*time)} : {x:1.2,v:0};
  }
  function advance(state, input, dt = DT) {
    const decay = Math.exp(-DRAG * dt), a = (1 - decay) / DRAG;
    return {x: state.x + state.v * a + input / DRAG * (dt - a),
      v: state.v * decay + input * a};
  }
  class Delay {
    constructor(steps) { this.values = Array(steps).fill(0); this.head = 0; }
    push(value) {
      if (!this.values.length) return value;
      const old = this.values[this.head];
      this.values[this.head] = value;
      this.head = (this.head + 1) % this.values.length;
      return old;
    }
    predict(state) {
      let predicted = {...state};
      for (let j = 0; j < this.values.length; j++)
        predicted = advance(predicted, this.values[(this.head + j) % this.values.length]);
      return predicted;
    }
  }
  class Ship {
    constructor(kind, steps) {
      this.kind = kind; this.line = new Delay(steps);
      this.state = {x: -1.8, v: 0}; this.sumSquares = 0; this.count = 0;
      this.command = 0; this.applied = 0;
    }
    step(target, settings, manual = 0) {
      let state = this.state, aim = target.x;
      if (this.kind === 'predictor') {
        state = this.line.predict(state);
        // A constant-velocity guess uses only the target's CURRENT velocity.
        // It cannot anticipate the next turn or a user's next drag.
        aim = clamp(target.x + target.v * this.line.values.length * DT, -3, 3);
      }
      const command = this.kind === 'manual' ? manual * LIMIT :
        settings.gain * (aim - state.x) - 2 * settings.damping * Math.sqrt(settings.gain) * state.v;
      this.command = clamp(command, -LIMIT, LIMIT);
      this.applied = this.line.push(this.command);
      this.state = advance(this.state, this.applied);
      const error = this.state.x - target.x;
      this.sumSquares += error * error; this.count++;
      return error;
    }
    get rmse() { return this.count ? Math.sqrt(this.sumSquares / this.count) : 0; }
  }
  class Experiment {
    constructor(settings) {
      this.settings = {...settings}; this.steps = Math.round(settings.delay / DT);
      this.delay = this.steps * DT; this.tick = 0; this.rows = [];
      this.ships = [new Ship('instant', 0), new Ship('delayed', this.steps),
        new Ship('predictor', this.steps), new Ship('manual', this.steps)];
    }
    step(target, manual = 0) {
      this.ships.forEach(ship => ship.step(target, this.settings, manual));
      this.tick++;
      // Every sample contains the parameters needed to reproduce the run.
      const row = [this.tick * DT, this.settings.gain, this.settings.damping, this.delay,
        target.x, target.v, this.settings.manual ? 1 : 0, manual];
      this.ships.forEach(ship => row.push(ship.state.x, ship.state.v, ship.command, ship.applied));
      this.rows.push(row); return row;
    }
    get time() { return this.tick * DT; }
  }
  const csvHeader = ['time_s','gain','damping_ratio','command_delay_s','target_x',
    'target_velocity','manual_visible','manual_input'];
  ['instant','delayed','predictor','manual'].forEach(name =>
    ['x','v','command','applied'].forEach(field => csvHeader.push(`${name}_${field}`)));
  const api = {DT, DRAG, LIMIT, advance, Delay, Ship, Experiment, csvHeader, clamp, presets, targetAt};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.StarLab = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
