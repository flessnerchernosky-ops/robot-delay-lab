'use strict';
(() => {
  const E = window.StarLab, $ = id => document.getElementById(id);
  const colors = ['#5cddd6','#ff9780','#b7a3ff','#f2ce7e'];
  const labels = ['立即反应','有延迟','预测反应','你来驾驶'];
  const presets = E.presets;
  let run, paused=false, previousTime=null, accumulator=0, dragTarget=1.2;
  let target={x:1.2,v:0}, keys=new Set(), buttons=new Set(), activePreset='gentle';
  const settings = () => ({delay:Number($('delay').value),gain:Number($('gain').value),
    damping:Number($('damping').value),motion:$('motion').value,manual:$('manual').checked});
  function refreshControls() {
    $('delay-value').textContent = `${run.delay.toFixed(2)} 秒`;
    $('gain-value').textContent = run.settings.gain.toFixed(1);
    $('damping-value').textContent = run.settings.damping.toFixed(2);
    $('manual-controls').hidden = !run.settings.manual;
    document.querySelectorAll('[data-preset]').forEach(button => {
      const selected = button.dataset.preset === activePreset;
      button.classList.toggle('selected',selected); button.setAttribute('aria-pressed',String(selected));
    });
  }
  function restart() {
    run = new E.Experiment(settings()); paused=false; previousTime=null; accumulator=0;
    dragTarget=1.2; target={x:1.2,v:0}; keys.clear(); buttons.clear();
    $('pause').textContent='暂停'; $('pause').disabled=false;
    $('download-state').textContent='记录保存在你的设备，页面不上传数据。';
    refreshControls(); updateScores(); draw();
  }
  function applyPreset(name) {
    activePreset=name; const preset=presets[name];
    ['delay','gain','damping','motion'].forEach(id => $(id).value=preset[id]);
    $('mission-copy').textContent=preset.text; restart();
  }
  document.querySelectorAll('[data-preset]').forEach(button =>
    button.addEventListener('click',()=>applyPreset(button.dataset.preset)));
  ['delay','gain','damping','motion','manual'].forEach(id => $(id).addEventListener('change',()=>{
    activePreset=null; $('mission-copy').textContent='自选实验：保持其他设置不变，一次只改一个变量。'; restart();
  }));
  ['delay','gain','damping'].forEach(id => $(id).addEventListener('input',()=>{
    const value=Number($(id).value);
    $(id+'-value').textContent=id==='delay'?`${value.toFixed(2)} 秒`:value.toFixed(id==='gain'?1:2);
  }));
  $('restart').addEventListener('click',restart);
  $('pause').addEventListener('click',()=>{
    paused=!paused; previousTime=null; accumulator=0;
    $('pause').textContent=paused?'继续':'暂停'; updateScores();
  });
  function pilotInput() {
    const left = keys.has('a')||keys.has('arrowleft')||buttons.has('left');
    const right = keys.has('d')||keys.has('arrowright')||buttons.has('right');
    return run.settings.manual ? Number(right)-Number(left) : 0;
  }
  ['left','right'].forEach(id=>{
    const button=$(id);
    button.addEventListener('pointerdown',event=>{
      event.preventDefault(); button.setPointerCapture(event.pointerId);
      buttons.add(id); button.classList.add('active');
    });
    const release=()=>{buttons.delete(id); button.classList.remove('active');};
    button.addEventListener('pointerup',release); button.addEventListener('pointercancel',release);
    button.addEventListener('lostpointercapture',release);
  });
  window.addEventListener('keydown',event=>{
    const editing = /^(SELECT|TEXTAREA)$/.test(event.target.tagName) ||
      (event.target.tagName === 'INPUT' && event.target.type !== 'checkbox');
    if (!run.settings.manual || editing) return;
    const key=event.key.toLowerCase();
    if (['a','d','arrowleft','arrowright'].includes(key)) {event.preventDefault();keys.add(key);}
  });
  window.addEventListener('keyup',event=>keys.delete(event.key.toLowerCase()));
  window.addEventListener('blur',()=>{
    keys.clear();buttons.clear();document.querySelectorAll('.pilot-buttons button').forEach(b=>b.classList.remove('active'));
    if (!paused && run.time < 20) {paused=true;$('pause').textContent='继续';updateScores();}
  });
  function starAt(time) {
    return run.settings.motion === 'drag' ? {x:dragTarget,v:0} : E.targetAt(time,run.settings.motion);
  }
  function drag(event) {
    const rect=$('space').getBoundingClientRect();
    const width=rect.width, left=85, right=width-24;
    dragTarget=E.clamp(((event.clientX-rect.left-left)/(right-left))*8-4,-3,3);
    if ($('motion').value !== 'drag') {
      $('motion').value='drag'; run.settings.motion='drag';activePreset=null;
      $('mission-copy').textContent='星星由你拖动。突然换位置时，飞船仍需要时间调整。';refreshControls();
    }
    target={x:dragTarget,v:0};
    // A dragged target is a new position command, not a noisy velocity estimate.
    if (paused) draw();
  }
  $('space').addEventListener('pointerdown',event=>{
    if (run.time>=20) return;
    $('space').setPointerCapture(event.pointerId);drag(event);
  });
  $('space').addEventListener('pointermove',event=>{
    if ($('space').hasPointerCapture(event.pointerId)) drag(event);
  });
  function surface(id) {
    const canvas=$(id), rect=canvas.getBoundingClientRect(), dpr=window.devicePixelRatio||1;
    const w=Math.max(1,rect.width),h=Math.max(1,rect.height);
    if (canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)) {
      canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
    }
    const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
    ctx.font='12px system-ui, "Microsoft YaHei", sans-serif'; return {ctx,w,h};
  }
  function star(ctx,x,y) {
    ctx.beginPath();for(let i=0;i<10;i++){
      const angle=-Math.PI/2+i*Math.PI/5,radius=i%2?4.5:10;
      const px=x+Math.cos(angle)*radius,py=y+Math.sin(angle)*radius;
      if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);
    }ctx.closePath();ctx.fillStyle='#f2ce7e';ctx.fill();
  }
  function drawSpace() {
    const {ctx,w,h}=surface('space'),left=85,right=w-24,span=right-left;
    const x=value=>left+(value+4)/8*span;
    for(let i=0;i<50;i++) {ctx.fillStyle=i%5?'#31415b':'#677b97';ctx.fillRect((i*137+31)%w,(i*71+21)%h,1.2,1.2);}
    const n=run.settings.manual?4:3,spacing=(h-45)/n;
    for(let j=0;j<n;j++){
      const y=38+spacing*(j+0.5),ship=run.ships[j],position=ship.state.x;
      ctx.strokeStyle='#29374c';ctx.setLineDash([4,7]);ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(right,y);ctx.stroke();ctx.setLineDash([]);
      ctx.fillStyle=colors[j];ctx.fillText(labels[j],14,y-15);ctx.fillStyle='#92a3bc';ctx.font='10px system-ui';
      ctx.fillText(j===0?'无等待':`等待 ${run.delay.toFixed(2)} s`,14,y+3);ctx.font='12px system-ui';
      const sx=x(E.clamp(position,-4,4)),tx=x(target.x);
      ctx.strokeStyle=colors[j]+'70';ctx.beginPath();ctx.moveTo(sx,y);ctx.lineTo(tx,y);ctx.stroke();
      star(ctx,tx,y);
      ctx.save();ctx.translate(sx,y);const direction=ship.state.v>=0?1:-1;ctx.scale(direction,1);
      if(Math.abs(ship.applied)>0.1){ctx.fillStyle='#f2ce7e';ctx.beginPath();ctx.moveTo(-12,-4);ctx.lineTo(-18-Math.min(10,Math.abs(ship.applied)),0);ctx.lineTo(-12,4);ctx.fill();}
      ctx.fillStyle=colors[j];ctx.beginPath();ctx.moveTo(15,0);ctx.lineTo(-11,-8);ctx.lineTo(-6,0);ctx.lineTo(-11,8);ctx.closePath();ctx.fill();ctx.restore();
      if(Math.abs(position)>4){ctx.fillStyle=colors[j];ctx.textAlign=position>0?'right':'left';ctx.fillText(`飞出画面 ${position.toFixed(1)}`,position>0?right:left,y-20);ctx.textAlign='left';}
    }
    ctx.fillStyle='#92a3bc';ctx.font='10px system-ui';ctx.fillText('−4',left,h-8);ctx.textAlign='center';ctx.fillText('0',x(0),h-8);ctx.textAlign='right';ctx.fillText('+4',right,h-8);ctx.textAlign='left';
  }
  function drawChart() {
    const {ctx,w,h}=surface('chart'),left=42,right=w-22,top=15,bottom=h-28;
    const rows=run.rows.filter((_,i)=>i%4===0 && run.time-(i+1)*E.DT<=10);
    const n=run.settings.manual?4:3;let scale=1;
    rows.forEach(row=>{for(let j=0;j<n;j++)scale=Math.max(scale,Math.abs(row[8+j*4]-row[4])*1.08);});
    const y=value=>(top+bottom)/2-value/scale*(bottom-top)/2;
    [scale,0,-scale].forEach(value=>{
      ctx.strokeStyle=value===0?'#62738c':'#27364b';ctx.beginPath();ctx.moveTo(left,y(value));ctx.lineTo(right,y(value));ctx.stroke();
      ctx.fillStyle='#9cabbd';ctx.font='10px system-ui';ctx.fillText(value.toFixed(1),5,y(value)+3);
    });
    const start=Math.max(0,run.time-10),duration=Math.max(10,run.time-start);
    for(let j=0;j<n;j++){
      ctx.strokeStyle=colors[j];ctx.lineWidth=1.8;ctx.beginPath();
      rows.forEach((row,i)=>{const px=left+(row[0]-start)/duration*(right-left),py=y(row[8+j*4]-row[4]);if(i)ctx.lineTo(px,py);else ctx.moveTo(px,py);});ctx.stroke();
    }
    ctx.lineWidth=1;ctx.fillStyle='#9cabbd';ctx.fillText(`${start.toFixed(0)} 秒`,left,h-6);ctx.textAlign='right';ctx.fillText(`${(start+duration).toFixed(0)} 秒`,right,h-6);ctx.textAlign='left';
  }
  function draw(){drawSpace();drawChart();}
  function updateScores() {
    ['instant','delayed','predictor','manual'].forEach((name,i)=>$('score-'+name).textContent=run.ships[i].count?run.ships[i].rmse.toFixed(2):'—');
    const finished=run.time>=20;
    $('run-state').textContent=finished?'本局完成':paused?'已暂停':'飞行中';
    $('timer').textContent=`${run.time.toFixed(1)} / 20 秒`;
    if(finished){$('pause').disabled=true;
      const delayed=run.ships[1].rmse,predicted=run.ships[2].rmse;
      $('observation').textContent=run.delay===0?'延迟为零时，三个自动方法完全同步。这是理解模型的起点。':
        `本局完成：有延迟 ${delayed.toFixed(2)}，预测 ${predicted.toFixed(2)}。${predicted<delayed?'这一次预测减少了典型偏离。':'这一次预测没有减少典型偏离。'}换一种目标运动再试；一局结果不代表所有场景。`;
    }else $('observation').textContent='曲线在零线上下反复穿越，表示追过头又折回来。纵轴会自动缩放，请同时看数字。';
    $('left').classList.toggle('active',pilotInput()<0);$('right').classList.toggle('active',pilotInput()>0);
  }
  $('export').addEventListener('click',()=>{
    if(!run.rows.length){$('download-state').textContent='先运行一点时间，再下载记录。';return;}
    const csv=E.csvHeader.join(',')+'\n'+run.rows.map(row=>row.join(',')).join('\n')+'\n';
    const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));
    const anchor=document.createElement('a');anchor.href=url;anchor.download='star-chase-experiment.csv';anchor.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('download-state').textContent=`已下载 ${run.rows.length} 个采样点（${run.time.toFixed(1)} 秒），包含设置、目标和推进指令。`;
  });
  window.addEventListener('resize',draw);
  function frame(now) {
    if(previousTime===null)previousTime=now;
    const elapsed=Math.min(0.1,(now-previousTime)/1000);previousTime=now;
    if(!paused && run.tick<2400){
      accumulator+=elapsed;
      while(accumulator>=E.DT && run.tick<2400){target=starAt(run.time);run.step(target,pilotInput());accumulator-=E.DT;}
    }
    updateScores();draw();requestAnimationFrame(frame);
  }
  applyPreset('gentle');requestAnimationFrame(frame);
})();
