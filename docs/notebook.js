/* Completed-run summaries and honest comparisons, shared by browser and checks. */
(function (root) {
  'use strict';
  const motions={fixed:'停在原地',wander:'左右巡游',fast:'快速折返',drag:'由我拖动'};
  const names={delay:'指令延迟',gain:'着急程度',damping:'刹车意愿'};
  function capture(run,notes={}) {
    if(run.tick!==2400 || run.rows.length!==2400) throw new Error('请先跑完 20 秒，再保存成绩。');
    return {settings:{delay:run.delay,gain:run.settings.gain,damping:run.settings.damping,
      motion:run.settings.motion,manual:Boolean(run.settings.manual)},
      duration:run.time,samples:run.rows.length,
      scores:run.ships.slice(0,3).map(ship=>ship.rmse),
      question:String(notes.question||'').trim(),guess:String(notes.guess||'').trim(),
      explanation:String(notes.explanation||'').trim()};
  }
  function compare(a,b) {
    if(!a||!b) return {eligible:false,text:'保存两局完整成绩后，就能对照自己的发现。'};
    if(a===b) return {eligible:false,text:'请选择两条不同的记录。'};
    if(a.settings.motion!==b.settings.motion || a.settings.motion==='drag' ||
        a.settings.manual || b.settings.manual)
      return {eligible:false,text:'这两局的目标运动不同，或包含拖动／手动驾驶。操作也会影响结果；请用同一种自动目标、关闭手动驾驶再比较参数。'};
    const changed=Object.keys(names).filter(key=>a.settings[key]!==b.settings[key]);
    if(changed.length>1) return {eligible:false,text:`这两局同时改变了${changed.map(key=>names[key]).join('、')}，无法把分数变化归因给其中一个设置。试试一次只改一个变量。`};
    const delta=b.scores[1]-a.scores[1];
    const change=Math.abs(delta)<1e-10?'相同':`${delta<0?'降低':'增加'} ${Math.abs(delta/a.scores[1]*100).toFixed(1)}%`;
    const setting=changed.length?`只改变${names[changed[0]]}：${a.settings[changed[0]]} → ${b.settings[changed[0]]}。`:'两局的设置相同，可检查重复运行是否一致。';
    return {eligible:true,changed,text:`${setting}有延迟飞船的典型偏离：${a.scores[1].toFixed(3)} → ${b.scores[1].toFixed(3)}（${change}）。这是当前模型、目标与 20 秒范围内的结果。`};
  }
  function markdown(entries) {
    const lines=['# 我的太空追星实验记录','','来源：https://flessnerchernosky-ops.github.io/robot-delay-lab/',
      '','这是我填写的实验笔记；请核对、补充后再用于项目展示。空白处不代表已经完成个人研究。',
      '','每局从同一起点运行 20 秒，2400 个采样点；典型偏离为 RMSE（仿真单位），包含起步过程。',
      '这是确定性的教学模型，重复同一设置不是独立随机实验；没有真实硬件验证。',
      '笔记只保存成绩摘要。完整轨迹请在对应那一局单独下载 CSV，文件名由你标注。',''];
    entries.forEach((entry,i)=>{
      const s=entry.settings;
      lines.push(`## 实验 ${i+1}`,'',`研究问题：${entry.question||'（待填写）'}`,'',
        `我的猜测：${entry.guess||'（待填写；建议开始前写）'}`,'',
        `设置：延迟 ${s.delay} 秒；着急程度 ${s.gain}；刹车意愿 ${s.damping}；目标 ${motions[s.motion]}；手动驾驶 ${s.manual?'开启':'关闭'}。`,'',
        '| 立即反应 | 有延迟 | 预测反应 |','|---:|---:|---:|',
        `| ${entry.scores.map(score=>score.toFixed(6)).join(' | ')} |`,'',
        `我的解释：${entry.explanation||'（待填写）'}`,'',
        '原始 CSV 文件： （请填入自己保存的文件名）','');
    });
    if(entries.length>=2) lines.push('## 最近两局的对照','',compare(entries.at(-2),entries.at(-1)).text,'');
    lines.push('## 展示前自己检查','',
      '- 我是否能解释：为什么停止推进后，飞船还会滑行？',
      '- 我是否区分了亲自运行的实验、预设示例和 AI 协助制作的内容？',
      '- 我是否只把结论写到实际比较过的目标、设置与模型范围？',
      '- 我下一步想改变什么，为什么？','');
    return lines.join('\n');
  }
  const api={capture,compare,markdown,motions};
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  else root.StarNotebook=api;
})(typeof globalThis!=='undefined'?globalThis:this);
