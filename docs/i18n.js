/* UI text only: switching languages never restarts or changes an experiment. */
(function(root){
  'use strict';
  let language=new URLSearchParams(location.search).get('lang')==='en'?'en':'zh';
  const dictionary={
    '← 三期项目总览':'← Explore all three episodes',
    '第二期 / 零基础互动篇':'EPISODE 2 / PLAY FIRST',
    '一颗星星，三种反应方式':'ONE STAR, THREE RESPONSES',
    '别追过头了':'Don’t overshoot',
    '太空追星实验':'Star Chase Lab',
    '为什么越着急追上目标，反而越容易来回晃？':'Why can trying harder make you wobble more?',
    '给飞船一点延迟，你就能亲眼看到答案。':'Add a command delay and watch what happens.',
    '不用安装 · 不用公式':'No installation · No equations needed',
    '先玩，再理解':'Play first, understand next',
    '★ 第三期：机械臂抓星星 / Catch the Stars →':'★ Episode 3: Catch the Stars →',
    '选择一段旅程':'Choose a journey',
    '实验场景':'Experiment scenarios',
    '① 轻松靠近':'① Gentle approach','② 越追越晃':'② More push, more wobble','③ 学会刹车':'③ Learn to brake','④ 星星也会走':'④ Moving star','⑤ 预测也会错':'⑤ Prediction can fail',
    '★ 共同目标':'★ Shared target','· 可在飞行区拖动星星':'· Drag the star in the flight area',
    '飞船位置动画。三行分别显示立即反应、延迟反应和预测反应；星星是共同目标。':'Spacecraft animation: instant, delayed and predictive responses pursue the same star.',
    '立即反应':'Instant response','有延迟':'Delayed response','预测反应':'Predictive response','你来驾驶':'Your spacecraft',
    '数字越小，整局离星星越近。把每一瞬间的距离汇总，得到“典型偏离距离”（RMSE，仿真单位）；包含起步过程。飞行结束后再公平比较。':'A smaller number means a smaller whole-run root-mean-square distance (RMSE, simulation units), including the initial approach. Compare after the flight finishes.',
    '飞船的性格':'Tune the spacecraft','每次改设置会从同一起点重新开始。':'Changing a setting restarts from the same initial state.',
    '指令多久才生效？':'Command delay','延迟期间，旧指令还在执行。':'Old commands keep executing while new commands wait.',
    '有多着急追上？':'Correction strength','着急程度越高，偏离一点就更用力。':'A larger gain produces more thrust for the same position error.',
    '有多愿意刹车？':'Braking strength','看见自己冲得快，就少踩油门。':'Moving too fast? Reduce the thrust.',
    '星星怎么走？':'Target motion','停在原地':'Fixed','左右巡游':'Slow orbit','快速折返':'Fast reversals','由我拖动':'Drag manually',
    '我也驾驶一艘':'Let me fly too',
    '长按按钮，或按 A / D、← / →。松开停止推进；仍会惯性滑行。你的指令也有同样的延迟。':'Hold a button, or use A / D or ← / →. Releasing stops thrust, but the spacecraft keeps sliding. Your commands have the same delay.',
    '向左推进':'Thrust left','向右推进':'Thrust right','← 左推':'← Left','右推 →':'Right →','你的典型偏离距离：':'Your RMSE:',
    '下载这一局的记录 ↓':'Download this run as CSV ↓',
    '谁还在来回晃？':'Who is still wobbling?','距星星的左右偏差 · 最近 10 秒':'Signed target error · Last 10 seconds',
    '偏差曲线：零线代表与星星重合。颜色与三艘飞船一致。':'Error curves: zero means at the target. Colors match the spacecraft.',
    '一条指令的旅程':'The journey of a command',
    '1 · 现在看见':'1 · Observe now','“星星在右边”':'“The star is to the right”','根据位置和速度，决定向右推多少。':'Use current position and velocity to choose thrust.',
    '2 · 排队等待':'2 · Wait in a queue','“新指令还没到”':'“The new command has not arrived”','飞船继续滑行，旧指令还在执行。':'The spacecraft keeps moving as old commands execute.',
    '3 · 终于生效':'3 · Execute later','“位置已经变了”':'“The position has already changed”','新指令按原计划执行，却可能已经推得太晚。':'The planned thrust executes, possibly too late.',
    '4 · 再次纠正':'4 · Correct again','“这次往左推”':'“Now push left”','纠正也要等待。用力过大时，就可能反复追过头。':'Corrections also wait. Excessive thrust can cause repeated overshoot.',
    '01 / 反馈':'01 / FEEDBACK','边看边改':'Observe and adjust',
    '发现星星在右边，就向右推；发现自己冲得太快，就刹车。“观察 → 调整 → 再观察”就是反馈。你调淋浴水温时，也在做类似的事。':'Push toward the star, and brake when moving too fast. Observe → adjust → observe is feedback. Adjusting shower temperature is a familiar analogy.',
    '02 / 延迟':'02 / DELAY','修正来晚了':'Corrections arrive late',
    '你刚刚想向右推，但飞船过一会儿才收到指令。等它收到时，你可能已经需要向左推了。越用力纠正，越可能来回追过头。':'A rightward command may arrive when leftward thrust is already needed. Stronger corrections can increase repeated overshoot.',
    '03 / 预测':'03 / PREDICTION','先想一想将来的位置':'Estimate where you will be',
    '紫色飞船会根据当前速度和排队中的指令，估计新指令生效时的位置。它还假设星星会暂时保持当前速度。突然转向时，这个猜测也会错。':'The purple spacecraft uses its current velocity and queued commands to estimate its future position. It assumes the star temporarily keeps its current velocity. Sudden turns can defeat this assumption.',
    '轮到你发现':'YOUR TURN TO DISCOVER','三个小挑战':'Three small challenges','把发现记下来 ↓':'Write down your findings ↓',
    '选“越追越晃”。其他设置不变，只把延迟降到 0，观察两条曲线。':'Choose “More push, more wobble”. Change only delay to 0 and compare the curves.',
    '把“愿意刹车”逐渐调高。是否越高就一定更好？用整局记录支持你的回答。':'Increase braking gradually. Is more always better? Use complete runs to support your answer.',
    '选“星星也会走”，再突然拖动星星。预测飞船会不会猜错？预测并不是偷看未来。':'Choose “Moving star”, then drag the star suddenly. Can prediction fail? It never sees future targets.',
    '从试玩到自己的发现':'FROM PLAY TO YOUR FINDINGS','我的实验笔记本':'My experiment notebook','15 分钟学习路线 ↗':'15-minute learning path ↗',
    '先写猜测，再跑完一局、记下解释。成绩会保留到你关闭或刷新页面；最多 12 条，请及时下载笔记。内容只在当前页面，不上传。':'Write a hypothesis, complete a run, then explain the results. Save up to 12 runs in this page; refreshing or closing clears them. Download your notes before leaving. Nothing is uploaded.',
    '我想弄清楚什么？':'My question','例如：延迟相同，多刹车会不会更稳？':'For example: with the same delay, does more braking help?',
    '我的猜测（建议开始前写）':'My hypothesis (write before running)','我猜……因为……':'I predict… because…',
    '看完成绩，我怎么解释？':'My explanation after the run','我观察到……它支持／不支持我的猜测……':'I observed… This supports / challenges my hypothesis…',
    '下载我的实验笔记 ↓':'Download my notes ↓',
    '还没有保存记录。运行结束后，点击保存；不会自动替你填写发现。':'No saved runs yet. Save after finishing; your findings are yours to write.',
    '已保存的实验成绩':'Saved experiment scores','实验':'Run','目标':'Target','延迟 / 着急 / 刹车':'Delay / Gain / Braking','原设置':'Baseline','新设置':'New settings',
    '只比较同一种自动目标、关闭手动驾驶、一次只改一个参数的两局。拖动与手动操作可以记录，但不能当作同条件的参数对照。':'Compare runs with the same automatic target, manual driving off, and exactly one parameter changed. Dragged and manually driven runs can be saved but are not controlled parameter comparisons.',
    '这是一个一维虚构飞船模型：有限推进力、微弱阻力、推进指令等待队列。三种自动方法共用参数；立即反应是零延迟参考。它帮助理解原理，不代表真实航天器或淋浴系统。':'A fictional one-dimensional spacecraft model with limited thrust, small drag and queued commands. Automatic methods share parameters; instant response is a zero-delay reference. It illustrates principles, not real spacecraft or shower dynamics.',
    '读完整的玩法、模型与复现实验 ↗':'Read the guide, model and reproducible experiments ↗',
    '开源 MIT · 无外部字体、追踪脚本或运行依赖 · AI 协助制作':'MIT open source · No external fonts, tracking scripts or runtime dependencies · AI-assisted',
    '暂停':'Pause','继续':'Resume','重来一局 ↻':'Restart ↻','本局成绩已保存':'Run saved','已保存 12 条，请下载笔记':'12 runs saved; download your notes','保存本局成绩':'Save this run','跑完 20 秒后保存成绩':'Complete 20 seconds to save',
    '本局完成':'Run complete','已暂停':'Paused','飞行中':'Flying','无等待':'No delay',
    '记录保存在你的设备，页面不上传数据。':'Records stay on your device. Nothing is uploaded.',
    '先运行一点时间，再下载记录。':'Run the experiment for a moment before downloading.',
    '延迟为零时，三个自动方法完全同步。这是理解模型的起点。':'With zero delay, all three automatic methods coincide. Start here to understand the model.',
    '曲线在零线上下反复穿越，表示追过头又折回来。纵轴会自动缩放，请同时看数字。':'Repeated zero crossings show overshoot and return. The vertical axis rescales; also check the numerical scores.',
    '自选实验：保持其他设置不变，一次只改一个变量。':'Custom experiment: change one variable at a time.',
    '星星由你拖动。突然换位置时，飞船仍需要时间调整。':'You control the star. After a sudden move, the spacecraft still needs time to respond.',
    '先看没有延迟时，飞船如何停在星星附近。三艘飞船应完全同步。':'With no delay, watch all three spacecraft approach together.',
    '新指令晚了 0.4 秒才生效。珊瑚色飞船会不会越纠正，越追过头？':'Commands arrive 0.4 seconds late. Does the coral spacecraft overshoot more as it corrects?',
    '只增加刹车意愿，其他条件和上一关一样。晃动变小了吗？':'Only braking is increased from the previous preset. Is the wobble smaller?',
    '星星开始转弯。紫色飞船只能猜它继续沿当前速度移动，并不知道下一次转弯。':'The star turns. The purple spacecraft assumes constant target velocity; it cannot foresee the next turn.',
    '目标快速折返，保持当前速度的猜测很快失效。跑完 20 秒，看看预测是否反而更差。':'Fast reversals break the constant-velocity assumption. Complete 20 seconds: can prediction be worse?',
    '保存两局完整成绩后，就能对照自己的发现。':'Save two complete runs to compare your findings.',
    '请选择两条不同的记录。':'Select two different runs.',
    '这两局的目标运动不同，或包含拖动／手动驾驶。操作也会影响结果；请用同一种自动目标、关闭手动驾驶再比较参数。':'Target motion differs, or a run includes dragging / manual driving. Use the same automatic target with manual driving off to compare parameters.',
    '指令延迟':'Command delay','着急程度':'Correction strength','刹车意愿':'Braking strength',
    '两局的设置相同，可检查重复运行是否一致。':'Settings are identical; check deterministic repeatability.',
  };
  function text(value){
    if(language!=='en')return value;
    if(dictionary[value])return dictionary[value];
    let result=value;
    const rules=[
      [/^([\d.]+) 秒$/,'$1 s'],[/^([\d.]+) \/ 20 秒$/,'$1 / 20 s'],[/^等待 ([\d.]+) s$/,'Delay $1 s'],[/^飞出画面 ([-\d.]+)$/,'Off screen $1'],
      [/^实验 (\d+)$/,'Run $1'],[/^(\d+) · 手动$/,'$1 · Manual'],
      [/^已下载 (\d+) 个采样点（([\d.]+) 秒），包含设置、目标和推进指令。$/,'Downloaded $1 samples ($2 s), including settings, targets and thrust commands.'],
      [/^已下载 (\d+) 条实验笔记。完整轨迹 CSV 请在对应那一局另行下载。$/,'Downloaded $1 notes. Download each full trajectory separately as CSV.'],
      [/^已保存实验 (\d+)，含 20 秒完整成绩和你当前填写的笔记。新一局开始前，请更新猜测与解释；保存后这条笔记不会随输入框改变。$/,'Saved run $1 with complete 20-second scores and your current notes. Update your hypothesis before the next run. Saved notes are independent snapshots.'],
      [/^本局完成：有延迟 ([\d.]+)，预测 ([\d.]+)。这一次预测(没有)?减少了典型偏离。换一种目标运动再试；一局结果不代表所有场景。$/,(_,a,b,no)=>`Run complete: delayed ${a}, predictive ${b}. Prediction ${no?'did not reduce':'reduced'} RMSE this time. Try another target: one run does not represent every scenario.`],
    ];
    for(const [pattern,replacement] of rules)if(pattern.test(value))return value.replace(pattern,replacement);
    if(value.startsWith('这两局同时改变了'))return 'Multiple parameters changed; the score change cannot be attributed to one setting. Change one variable at a time.';
    if(value.includes('有延迟飞船的典型偏离：')){
      result=result.replace('只改变','Only ').replace('：',': ').replace('。有延迟飞船的典型偏离：','. Delayed spacecraft RMSE: ').replace('有延迟飞船的典型偏离：','Delayed spacecraft RMSE: ').replace('（',' (').replace('）。这是当前模型、目标与 20 秒范围内的结果。','). This result applies to the current model, target and 20-second interval.').replace('降低','decreased by').replace('增加','increased by').replace('相同','unchanged');
      for(const key of ['两局的设置相同，可检查重复运行是否一致。','指令延迟','着急程度','刹车意愿'])result=result.replace(key,dictionary[key]);
      return result;
    }
    return result;
  }
  const dynamic=new Set(['mission-copy','run-state','timer','delay-value','gain-value','damping-value','pause','download-state','observation','save-run','notebook-state','notebook-rows','compare-base','compare-new','comparison']);
  const nodes=[];const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){
    const node=walker.currentNode;
    if(!node.textContent.trim()||node.parentElement.closest('script,style,[data-language]'))continue;
    let ancestor=node.parentElement,skip=false;
    while(ancestor){if(dynamic.has(ancestor.id)){skip=true;break;}ancestor=ancestor.parentElement;}
    if(!skip)nodes.push([node,node.textContent]);
  }
  const attributes=[];
  document.querySelectorAll('[aria-label],[placeholder]').forEach(el=>{
    for(const key of ['aria-label','placeholder'])if(el.hasAttribute(key))attributes.push([el,key,el.getAttribute(key)]);
  });
  function render(){
    document.documentElement.lang=language==='en'?'en':'zh-CN';
    document.title=language==='en'?'Star Chase Lab · Robot Delay Lab':'别追过头了 · 太空追星实验';
    for(const [node,original] of nodes){const trimmed=original.trim();node.textContent=original.replace(trimmed,text(trimmed));}
    for(const [el,key,original] of attributes)el.setAttribute(key,text(original));
    document.querySelectorAll('[data-language]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.language===language)));
    document.getElementById('all-episodes').href='showcase.html?lang='+language;
    document.getElementById('arm-link').href='arm/?lang='+language;
    document.getElementById('learning-guide').href='https://github.com/flessnerchernosky-ops/robot-delay-lab/blob/main/LEARNING_MISSIONS'+(language==='en'?'.en':'')+'.md';
    document.getElementById('episode-guide').href='https://github.com/flessnerchernosky-ops/robot-delay-lab/blob/main/EPISODE_02'+(language==='en'?'.en':'')+'.md';
    document.querySelector('meta[name="description"]').content=language==='en'?'Play with feedback, command delay and prediction in a bilingual browser spacecraft lab. No installation or hardware.':'零基础也能玩的双语飞船实验：体验反馈、指令延迟与预测，无需安装或硬件。';
  }
  document.querySelectorAll('[data-language]').forEach(button=>button.addEventListener('click',()=>{
    language=button.dataset.language;const url=new URL(location.href);url.searchParams.set('lang',language);history.replaceState(null,'',url);
    render();window.dispatchEvent(new Event('starlanguagechange'));
  }));
  root.StarI18n={text,get language(){return language;}};render();
})(window);
