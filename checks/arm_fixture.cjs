'use strict';
// Unsaturated fixed-target fixture for the independent Python linear-system check.
const E=require('../docs/arm/engine.js'),run=new E.Experiment({...E.presets.reach,kp:2,kd:1,speed:100,target:E.fk([-.35,1.6])});
run.finish();process.stdout.write(JSON.stringify({settings:run.settings,dt:run.dt,initial_q:[-.55,1.8],reference_q:[-.35,1.6],rows:run.rows}));
