'use strict';
// Reproduce the exact browser presets without running a browser.
const fs=require('node:fs'), path=require('node:path');
const E=require('../docs/engine.js');
const out=path.join(__dirname,'..','examples');fs.mkdirSync(out,{recursive:true});
const summary=['preset,gain,damping_ratio,delay_s,instant_rmse,delayed_rmse,predictor_rmse'];
for(const [name,preset] of Object.entries(E.presets)){
  const run=new E.Experiment(preset);
  for(let i=0;i<2400;i++){
    const t=run.time;
    const target=E.targetAt(t,preset.motion);
    run.step(target);
  }
  summary.push([name,preset.gain,preset.damping,run.delay,...run.ships.slice(0,3).map(s=>s.rmse)].join(','));
  if(name==='chaos')fs.writeFileSync(path.join(out,'star_chase_chaos.csv'),
    E.csvHeader.join(',')+'\n'+run.rows.map(row=>row.join(',')).join('\n')+'\n');
}
fs.writeFileSync(path.join(out,'star_chase_summary.csv'),summary.join('\n')+'\n');
console.log(summary.join('\n'));
