'use strict';
const assert=require('node:assert/strict');
const E=require('../docs/engine.js');
let passed=0;
function check(name,fn){fn();passed++;console.log(`PASS ${name}`);}
const near=(a,b,tol=1e-9)=>assert.ok(Math.abs(a-b)<tol,`${a} != ${b}`);
check('zero thrust follows the analytic drag solution',()=>{
  const result=E.advance({x:1,v:2},0,0.7);
  near(result.v,2*Math.exp(-E.DRAG*0.7));
  near(result.x,1+2/E.DRAG*(1-Math.exp(-E.DRAG*0.7)));
});
check('constant thrust composition is independent of step subdivision',()=>{
  const a=E.advance({x:1,v:-0.5},3,0.4);
  const b=E.advance(E.advance({x:1,v:-0.5},3,0.2),3,0.2);
  near(a.x,b.x);near(a.v,b.v);
});
check('delay pulse arrives at the declared sample',()=>{
  const line=new E.Delay(3);assert.deepEqual([1,0,0,0,0].map(x=>line.push(x)),[0,0,0,1,0]);
  assert.equal(new E.Delay(0).push(4),4);
});
check('prediction uses queued inputs in chronological order without mutation',()=>{
  const line=new E.Delay(3);line.push(1);line.push(2);line.push(3);line.push(4);
  const state={x:0.1,v:0.4},before=JSON.stringify(line);
  const predicted=line.predict(state);
  const expected=[2,3,4].reduce((s,u)=>E.advance(s,u),state);
  near(predicted.x,expected.x);near(predicted.v,expected.v);
  assert.equal(JSON.stringify(line),before);assert.deepEqual(state,{x:0.1,v:0.4});
});
function simulate(settings,target=t=>({x:1.2,v:0})){
  const run=new E.Experiment(settings);
  for(let i=0;i<2400;i++)run.step(target(run.time));return run;
}
check('all three automatic methods are identical at zero delay',()=>{
  const run=simulate({delay:0,gain:4,damping:0.7},t=>({x:Math.cos(t),v:-Math.sin(t)}));
  assert.deepEqual(run.ships[0].state,run.ships[1].state);
  assert.deepEqual(run.ships[0].state,run.ships[2].state);
  assert.equal(run.ships[0].rmse,run.ships[2].rmse);
});
check('known queued-input prediction matches the future plant state',()=>{
  const line=new E.Delay(4);[1,-2,3,-1].forEach(u=>line.push(u));
  let state={x:1,v:-0.5};const predicted=line.predict(state);
  for(const futureCommand of [5,2,-3,4])state=E.advance(state,line.push(futureCommand));
  near(state.x,predicted.x);near(state.v,predicted.v);
});
check('manual commands are delayed and acceleration limited',()=>{
  const ship=new E.Ship('manual',2),settings={gain:4,damping:0.7};
  ship.step({x:0,v:0},settings,1);assert.equal(ship.applied,0);
  ship.step({x:0,v:0},settings,0);assert.equal(ship.applied,0);
  ship.step({x:0,v:0},settings,0);assert.equal(ship.applied,E.LIMIT);
});
check('the braking lesson changes one parameter and reduces error in that preset',()=>{
  const a=simulate({delay:0.4,gain:4,damping:0.2});
  const b=simulate({delay:0.4,gain:4,damping:0.7});
  assert.ok(b.ships[1].rmse<a.ships[1].rmse);
  assert.ok(a.ships[2].rmse<a.ships[1].rmse);
});
check('the rapid-turn preset exposes a prediction failure',()=>{
  const preset=E.presets.surprise;
  const run=simulate(preset,t=>E.targetAt(t,preset.motion));
  assert.ok(run.ships[2].rmse>run.ships[1].rmse);
});
check('complete records reproduce a moving target and manual inputs',()=>{
  const run=new E.Experiment({delay:0.6,gain:4,damping:0.7,manual:true});
  for(let i=0;i<2400;i++)run.step({x:1.2*Math.cos(0.65*run.time),v:-0.78*Math.sin(0.65*run.time)},i%300<100?1:-1);
  const replay=new E.Experiment(run.settings);
  run.rows.forEach(row=>replay.step({x:row[4],v:row[5]},row[7]));
  assert.deepEqual(replay.rows,run.rows);assert.equal(run.rows.length,2400);
  run.rows.forEach(row=>{assert.equal(row.length,E.csvHeader.length);assert.ok(row.every(Number.isFinite));
    for(let j=0;j<4;j++){assert.ok(Math.abs(row[10+4*j])<=E.LIMIT);assert.ok(Math.abs(row[11+4*j])<=E.LIMIT);}});
});
console.log(`${passed} meaningful model and reproducibility checks passed.`);
