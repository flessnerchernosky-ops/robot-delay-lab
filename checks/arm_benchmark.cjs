'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict'),E=require('../docs/arm/engine.js');
const manifest=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../examples/arm/manifest.json'),'utf8'));
const lines=fs.readFileSync(require('node:path').join(__dirname,'../examples/arm/summary.csv'),'utf8').trim().split('\n'),headers=lines.shift().split(',');
const rows=lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[headers[i],v])));
assert.equal(manifest.model,'arm-lab-v1');assert.equal(manifest.dt,E.DT);assert.equal(manifest.duration,E.DURATION);assert.equal(rows.length,manifest.cases.length*2);assert.equal(new Set(manifest.cases.map(c=>c.case)).size,manifest.cases.length);
for(const c of manifest.cases){const r=new E.Experiment(c.settings,c.dt);r.finish();assert.equal(c.interactive,false);assert.deepEqual(c.targets,[]);assert.deepEqual(c.initialSettings,c.settings);
  for(const actual of r.arms.map(a=>a.metrics())){const recorded=c.metrics.find(m=>m.kind===actual.kind),csv=rows.filter(row=>row.case===c.case&&row.kind===actual.kind);assert.equal(csv.length,1);const row=csv[0];
    for(const [key,value] of Object.entries(actual)){if(key==='kind'){assert.equal(row[key],value);continue;}if(value===null){assert.equal(recorded[key],null);assert.equal(row[key],'');}else{assert.ok(Math.abs(recorded[key]-value)<1e-8,`${c.case}: ${key}`);assert.ok(Math.abs(Number(row[key])-value)<1e-8,`${c.case}: CSV ${key}`);}}
    for(const k of ['kp','kd','delay','speed'])assert.equal(Number(row[k]),c.settings[k]);for(const k of ['limited','motion'])assert.equal(row[k],String(c.settings[k]));assert.equal(Number(row.target_x),c.settings.target.x);assert.equal(Number(row.target_y),c.settings.target.y);
  }
}
console.log(`PASS all ${manifest.cases.length} saved settings / ${rows.length} trajectories match their reproducible metrics.`);
