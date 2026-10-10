/* Original educational model. No third-party implementation is copied. */
(function(root){
  'use strict';
  const DT=0.01,DURATION=12,L1=1,L2=0.8,DRAG=0.3,TORQUE=6,TOLERANCE=0.06;
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const presets={
    reach:{kp:8,kd:4,delay:0,speed:2,limited:false,motion:'fixed',target:{x:1.1,y:0.65}},
    overshoot:{kp:16,kd:1.5,delay:0,speed:3,limited:false,motion:'fixed',target:{x:1.1,y:0.65}},
    delay:{kp:12,kd:4,delay:0.35,speed:2,limited:false,motion:'fixed',target:{x:1.1,y:0.65}},
    limits:{kp:8,kd:4,delay:0,speed:1.5,limited:true,motion:'fixed',target:{x:-1.15,y:0.8}},
    orbit:{kp:8,kd:4,delay:0.1,speed:2,limited:false,motion:'orbit',target:{x:1.1,y:0.65}}
  };
  function fk(q){return {x:L1*Math.cos(q[0])+L2*Math.cos(q[0]+q[1]),y:L1*Math.sin(q[0])+L2*Math.sin(q[0]+q[1])};}
  function bounds(limited){return limited?[[-1.4,1.4],[0.15,2.7]]:[[-Math.PI,Math.PI],[0,Math.PI]];}
  function ik(target,limited=false){
    const r=Math.hypot(target.x,target.y),radius=clamp(r,Math.abs(L1-L2)+1e-9,L1+L2-1e-9);
    const theta=r>1e-12?Math.atan2(target.y,target.x):0;
    const q2=Math.acos(clamp((radius*radius-L1*L1-L2*L2)/(2*L1*L2),-1,1));
    const q1=theta-Math.atan2(L2*Math.sin(q2),L1+L2*Math.cos(q2));
    // Normalize this fixed positive-elbow solution; other branches are not searched.
    const raw=[Math.atan2(Math.sin(q1),Math.cos(q1)),q2],b=bounds(limited);
    const q=raw.map((a,i)=>clamp(a,...b[i]));
    return {q,raw,reachable:r>=Math.abs(L1-L2)-1e-9&&r<=L1+L2+1e-9,
      limited:raw.some((a,i)=>a<b[i][0]-1e-9||a>b[i][1]+1e-9),radius:r};
  }
  function targetAt(time,s){return s.motion==='orbit'?{x:1+0.3*Math.cos(0.65*time),y:0.65+0.3*Math.sin(0.65*time)}:{...s.target};}
  function free(q,v,u,dt){const e=Math.exp(-DRAG*dt),h=-Math.expm1(-DRAG*dt)/DRAG;
    return {q:q+v*h+u/DRAG*(dt-h),v:v*e+u*h};}
  function advance(q,v,u,dt,speed,limit){
    v=clamp(v,-speed,speed);let next=free(q,v,u,dt),speedHit=false;
    if(Math.abs(next.v)>speed){
      const cap=Math.sign(next.v)*speed,equilibrium=u/DRAG;
      const ratio=(cap-equilibrium)/(v-equilibrium);
      const hit=ratio>0?clamp(-Math.log(ratio)/DRAG,0,dt):0;
      const partial=free(q,v,u,hit);next={q:partial.q+cap*(dt-hit),v:cap};speedHit=true;
    }
    let stop=false;
    if(next.q<limit[0]){next.q=limit[0];next.v=Math.max(0,next.v);stop=true;}
    if(next.q>limit[1]){next.q=limit[1];next.v=Math.min(0,next.v);stop=true;}
    return {...next,speedHit,stop};
  }
  class Delay{
    constructor(n){this.queue=Array.from({length:n},()=>[0,0]);this.head=0;}
    push(u){if(!this.queue.length)return [...u];const old=this.queue[this.head];this.queue[this.head]=[...u];this.head=(this.head+1)%this.queue.length;return old;}
  }
  class Arm{
    constructor(kind,s,dt){this.kind=kind;this.q=[-0.55,1.8];this.v=[0,0];this.line=new Delay(Math.round(s.delay/dt));this.u=[0,0];this.command=[0,0];this.sumSq=0;this.lateSq=0;this.count=0;this.lateCount=0;this.timeNear=0;this.catchTime=null;this.hold=0;this.stopSteps=0;this.speedSteps=0;this.torqueSteps=0;this.trace=[];}
    step(ref,target,s,time,dt){
      const raw=this.q.map((q,i)=>s.kp*(ref.q[i]-q)-(this.kind==='pd'?s.kd*this.v[i]:0));
      this.command=raw.map(u=>clamp(u,-TORQUE,TORQUE));this.u=this.line.push(this.command);
      const next=this.q.map((q,i)=>advance(q,this.v[i],this.u[i],dt,s.speed,bounds(s.limited)[i]));
      this.q=next.map(x=>x.q);this.v=next.map(x=>x.v);
      const endpoint=fk(this.q),error=Math.hypot(endpoint.x-target.x,endpoint.y-target.y);
      this.sumSq+=error*error;this.count++;
      if(time>8+1e-9){this.lateSq+=error*error;this.lateCount++;}
      if(error<=TOLERANCE){this.timeNear+=dt;this.hold+=dt;}else this.hold=0;
      if(this.catchTime===null&&this.hold>=0.5-1e-9)this.catchTime=time;
      this.stopSteps+=Number(next.some(x=>x.stop));this.speedSteps+=Number(next.some(x=>x.speedHit));this.torqueSteps+=Number(raw.some(u=>Math.abs(u)>TORQUE));
      this.trace.push(endpoint);if(this.trace.length>180)this.trace.shift();
      return {time,kind:this.kind,target_x:target.x,target_y:target.y,ref_q1:ref.q[0],ref_q2:ref.q[1],q1:this.q[0],q2:this.q[1],v1:this.v[0],v2:this.v[1],command1:this.command[0],command2:this.command[1],applied1:this.u[0],applied2:this.u[1],x:endpoint.x,y:endpoint.y,error,reachable:Number(ref.reachable),branch_limited:Number(ref.limited)};
    }
    metrics(){return {kind:this.kind,rmse:this.count?Math.sqrt(this.sumSq/this.count):null,late_rmse:this.lateCount?Math.sqrt(this.lateSq/this.lateCount):null,near_seconds:this.timeNear,catch_time:this.catchTime,joint_stop_steps:this.stopSteps,speed_limit_steps:this.speedSteps,torque_limit_steps:this.torqueSteps};}
  }
  function settings(input={}){
    const s={...presets.reach,...input,target:{...(input.target||presets.reach.target)}};
    for(const k of ['kp','kd','delay','speed'])if(!Number.isFinite(s[k]))throw new Error('Non-finite setting: '+k);
    if(s.kp<0||s.kd<0||s.delay<0||s.speed<=0||s.delay>2)throw new Error('Setting outside model domain');
    if(!Number.isFinite(s.target.x)||!Number.isFinite(s.target.y))throw new Error('Invalid target');
    if(!['fixed','orbit','drag'].includes(s.motion))throw new Error('Invalid target motion');
    s.limited=Boolean(s.limited);return s;
  }
  class Experiment{
    constructor(input,dt=DT){if(!Number.isFinite(dt)||dt<=0||Math.abs(DURATION/dt-Math.round(DURATION/dt))>1e-6)throw new Error('Invalid time step');this.dt=dt;this.settings=settings(input);this.initialSettings=JSON.parse(JSON.stringify(this.settings));this.stepCount=0;this.arms=['p','pd'].map(k=>new Arm(k,this.settings,dt));this.rows=[];this.target=targetAt(0,this.settings);this.ref=ik(this.target,this.settings.limited);this.interactive=false;this.targets=[];}
    get time(){return this.stepCount*this.dt;}
    get done(){return this.stepCount>=Math.round(DURATION/this.dt);}
    setTarget(target){this.settings.target={...target};this.settings.motion='drag';this.interactive=true;this.targets.push({time:this.time,...target});this.target={...target};this.ref=ik(target,this.settings.limited);}
    step(){if(this.done)return false;const time=(this.stepCount+1)*this.dt;
      // Target sampled at the interval start; error scored at its end.
      const controlTarget=targetAt(this.time,this.settings),ref=ik(controlTarget,this.settings.limited);
      this.target=targetAt(time,this.settings);this.ref=ik(this.target,this.settings.limited);
      for(const arm of this.arms)this.rows.push(arm.step(ref,this.target,this.settings,time,this.dt));
      this.stepCount++;return true;}
    finish(){while(this.step());return this.arms.map(a=>a.metrics());}
    snapshot(){if(!this.done)throw new Error('Only completed runs can be saved');return {settings:JSON.parse(JSON.stringify(this.settings)),initialSettings:JSON.parse(JSON.stringify(this.initialSettings)),dt:this.dt,interactive:this.interactive,targets:[...this.targets],metrics:this.arms.map(a=>a.metrics())};}
  }
  function csv(run){const headers=['time','kind','target_x','target_y','ref_q1','ref_q2','q1','q2','v1','v2','command1','command2','applied1','applied2','x','y','error','reachable','branch_limited'];
    return '# arm-lab-v1 '+JSON.stringify({settings:run.settings,initialSettings:run.initialSettings,dt:run.dt,complete:run.done,interactive:run.interactive,targets:run.targets})+'\n'+headers.join(',')+'\n'+run.rows.map(row=>headers.map(k=>typeof row[k]==='number'?row[k].toPrecision(12):row[k]).join(',')).join('\n')+'\n';}
  function comparable(a,b){if(a.interactive||b.interactive||a.settings.motion==='drag'||b.settings.motion==='drag')return {ok:false,reason:'interactive'};
    if(JSON.stringify(a.settings.target)!==JSON.stringify(b.settings.target)||a.settings.motion!==b.settings.motion||a.dt!==b.dt)return {ok:false,reason:'target'};
    const changed=['kp','kd','delay','speed','limited'].filter(k=>a.settings[k]!==b.settings[k]);return {ok:changed.length===1,reason:changed.length===0?'same':'multiple',changed};}
  const api={DT,DURATION,L1,L2,DRAG,TORQUE,TOLERANCE,presets,clamp,fk,ik,bounds,free,advance,Delay,Arm,Experiment,csv,comparable};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ArmLab=api;
})(typeof window==='undefined'?globalThis:window);
