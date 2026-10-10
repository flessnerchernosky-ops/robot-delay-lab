'use strict';
const fs=require('node:fs'),path=require('node:path'),E=require('../docs/arm/engine.js');
const out=path.join(__dirname,'../examples/arm');fs.mkdirSync(out,{recursive:true});
const cases=Object.entries(E.presets).map(([name,settings])=>({name,settings}));
for(const delay of [0,.05,.1,.2,.3,.4,.5,.6])for(const kp of [8,16])cases.push({name:`delay-${delay}-kp-${kp}`,settings:{...E.presets.reach,kp,delay}});
for(const kd of [0,.5,1,2,4,8])cases.push({name:`braking-${kd}`,settings:{...E.presets.reach,kd}});
for(const speed of [.5,1,2,3])cases.push({name:`speed-${speed}`,settings:{...E.presets.reach,speed}});
const headers=['case','kind','kp','kd','delay','speed','limited','motion','target_x','target_y','rmse','late_rmse','near_seconds','catch_time','joint_stop_steps','speed_limit_steps','torque_limit_steps'];
const lines=[headers.join(',')],manifest=[];
for(const c of cases){const r=new E.Experiment(c.settings);const metrics=r.finish();manifest.push({case:c.name,...r.snapshot()});for(const m of metrics){const row={case:c.name,...r.settings,target_x:r.settings.target.x,target_y:r.settings.target.y,...m};lines.push(headers.map(k=>row[k]===null?'':row[k]).join(','));}}
fs.writeFileSync(path.join(out,'summary.csv'),lines.join('\n')+'\n');fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({model:'arm-lab-v1',dt:E.DT,duration:E.DURATION,cases:manifest},null,2)+'\n');
console.log(`${cases.length} deterministic cases / ${cases.length*2} trajectories saved to examples/arm.`);
