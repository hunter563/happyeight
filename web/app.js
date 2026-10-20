const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=ns=>(ns||[]).map(n=>String(n).padStart(2,'0')).join(' ')||'—';
const balls=ns=>`<div class="balls">${(ns||[]).map(n=>`<span class="ball">${String(n).padStart(2,'0')}</span>`).join('')}</div>`;
const metric=(label,value,note='')=>`<div class="metric"><small>${esc(label)}</small><strong>${esc(value)}</strong><em>${esc(note)}</em></div>`;
function message(text,error=false){$('message').textContent=text;$('message').classList.toggle('error',error);}
async function api(url,body){const r=await fetch(url,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await r.json();if(!r.ok)throw new Error(data.error||'请求失败');return data;}
async function busy(id,task){const b=$(id),old=b.textContent;b.disabled=true;b.textContent='处理中…';try{await task();}catch(e){message(e.message,true);}finally{b.disabled=false;b.textContent=old;}}
function tab(name){if(!['prediction','backtest','overview','records','charts'].includes(name))name='prediction';document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('active',p.id===name));if(name==='records')loadRecords().catch(e=>message(e.message,true));if(name==='charts')loadCharts().catch(e=>message(e.message,true));}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{location.hash=b.dataset.tab;tab(b.dataset.tab);});
window.addEventListener('hashchange',()=>tab(location.hash.slice(1)));tab(location.hash.slice(1));
async function refresh(){
 const s=await api('/api/status');
 $('prediction-context').textContent=s.latest?`数据截至 ${s.latest.issue} 期（${s.latest.date}）；${s.prediction.suggestedNextIssue?'目标推算为 '+s.prediction.suggestedNextIssue+' 期。':'请核对目标期号。'}`:'请先同步或导入开奖';
 $('predict-issue').placeholder=s.prediction.suggestedNextIssue?`自动推算：${s.prediction.suggestedNextIssue}`:'请填写目标期号';
 $('metrics').innerHTML=metric('有效历史样本',s.count.toLocaleString(),'每期20个开奖号')+metric('数据截止期',s.latest?.issue||'暂无',s.latest?.date||'')+metric('启用预测规则','1','上上期±1 · 固定评分')+metric('保留候选数量','10–14','由同一数量策略确定');
 $('draw-label').textContent=s.latest?`${s.latest.issue} · ${s.latest.date}`:'暂无';$('latest-balls').innerHTML=balls(s.latest?.numbers);$('source-note').textContent=s.latest?`来源：${s.latest.source}`:'';
 $('history').innerHTML=s.recent.map(r=>`<tr><td>${esc(r.issue)}</td><td>${esc(r.date)}</td><td class="numbers">${fmt(r.numbers)}</td></tr>`).join('');
 if(s.ageDays>1)message(`开奖数据已过期${s.ageDays}天，请先同步。`,true);
}
$('sync').onclick=()=>busy('sync',async()=>{const r=await api('/api/sync',{});await refresh();message(`同步完成：新增${r.inserted}期，重复${r.duplicates}期。`);});
$('import-file').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{if(f.size>1800000)throw Error('请拆分到1.8MB以内');const text=await f.text();const r=await api('/api/import',f.name.endsWith('.json')?{draws:JSON.parse(text)}:{csv:text});await refresh();message(`已导入${r.inserted}期。`);}catch(err){message(err.message,true);}e.target.value='';};
$('run-predict').onclick=()=>busy('run-predict',async()=>{
 $('prediction-progress').textContent='正在更新数据并执行固定评分规则…';$('prediction-result').className='empty';$('prediction-result').textContent='等待本次结果…';
 try{
  const r=await api('/api/predict',{targetIssue:$('predict-issue').value.trim()||null,sync:$('predict-sync').checked});
  const selected=r.selections.locked_rf;
  $('prediction-result').className='prediction-result';
  $('prediction-result').innerHTML=`<div class="prediction-heading"><div><small>本次预测目标</small><h2>第 ${esc(r.targetIssue)} 期</h2></div><span>已保存 #${r.recordId}</span></div><p class="muted">使用截至${esc(r.asOfIssue)}期的12期历史；原始候选来自${esc(r.sourceIssue)}期±1。</p><h3>最终保留 ${r.k} 个</h3>${balls(selected)}<p>删除 ${r.deletedCandidates.length} 个：${fmt(r.deletedCandidates)}</p><details><summary>查看20个候选的评分</summary><p>原20号：${fmt(r.baseCandidates)}</p><div class="table-scroll"><table><thead><tr><th>号码</th><th>排序评分</th><th>处理</th></tr></thead><tbody>${[...r.scores].sort((a,b)=>b.score-a.score).map(s=>`<tr><td>${String(s.number).padStart(2,'0')}</td><td>${s.score.toFixed(5)}</td><td>${s.selected?'保留':'删除'}</td></tr>`).join('')}</tbody></table></div><p class="muted">${esc(r.scoreMeaning)}</p></details>${r.sync.status==='error'?`<p class="note">${esc(r.sync.message)}</p>`:''}<p class="muted">${esc(r.targetNote)} 版本：${esc(r.version)}</p><a class="button secondary" href="#records">查看记录与复盘</a>`;
  $('prediction-progress').textContent=`已保存第${r.targetIssue}期预测。`;
  try{await refresh();message(`预测已保存：${r.k}个号码。`);}catch(e){message(`预测已保存，但数据概览刷新失败：${e.message}`,true);}
 }catch(e){$('prediction-progress').textContent='本次未生成预测。';throw e;}
});
$('run-test').onclick=()=>busy('run-test',async()=>{
 message('正在按同一固定规则逐期复核…');
 const r=await api('/api/backtest',{folds:Number($('test-folds').value)}),s=r.summary;
 $('test-result').className='';$('test-result').innerHTML=`<div class="note">${esc(r.note)}</div><p>${esc(r.firstIssue)}—${esc(r.lastIssue)}，实际${r.folds}期${r.folds<r.requestedFolds?'（训练截止期之后仅有这些可复核期数）':''}。</p><div class="metrics">${metric('平均保留',s.meanCount.toFixed(2))}${metric('平均命中',s.meanHits.toFixed(2))}${metric('累计命中',s.hits,`命中率 ${(s.rate*100).toFixed(2)}%`)}${metric('不足3个的期数',s.below3,`最低${s.minHits}个，最高${s.maxHits}个`)}</div><div class="table-scroll"><table><thead><tr><th>目标期号</th><th>历史截止</th><th>保留数</th><th>命中数</th><th>保留号码</th><th>命中号码</th><th>误删中奖号</th></tr></thead><tbody>${[...r.records].reverse().map(x=>`<tr><td>${esc(x.issue)}</td><td>${esc(x.trainThrough)}</td><td>${x.count}</td><td><b>${x.hits}</b></td><td class="numbers">${fmt(x.selected)}</td><td class="numbers">${fmt(x.matched)}</td><td class="numbers">${fmt(x.falseDeleted)}</td></tr>`).join('')}</tbody></table></div>`;
 message('固定规则回测完成。');
});
function renderRecords(rows,archived=false){return rows.map(r=>`<div class="record"><div class="section-head"><h3>#${r.id} · 目标 ${esc(r.target_issue)}</h3><span>${r.settled?'已匹配开奖':'等待开奖'}</span></div><p class="muted">保存于${esc(r.created_at)} · 数据截至${esc(r.as_of_issue)} · ${archived?'旧版归档':'固定规则'}</p>${Object.entries(r.payload.selections).map(([key,ns])=>`${archived?`<p>${esc(key)}</p>`:''}${balls(ns)}${r.settled?`<p>命中 <b>${r.hits[key]} / ${ns.length}</b></p>`:''}`).join('')}<details><summary>记录版本</summary><p>${esc(r.payload.version||'旧版')}</p><code>${esc(r.data_hash)}</code></details></div>`).join('')||'<p class="empty">暂无此类记录。生成下一期预测后会显示在这里。</p>';}
async function loadRecords(){const rows=await api('/api/experiments');$('records-result').className='';$('records-result').innerHTML=renderRecords(rows);}
$('reload-records').onclick=()=>busy('reload-records',loadRecords);
$('load-archive').onclick=()=>busy('load-archive',async()=>{$('archive-result').innerHTML=renderRecords((await api('/api/experiments?includeArchived=1')).filter(r=>r.archived),true);});
refresh().catch(e=>message(e.message,true));

let cachedCharts=null;
$('charts-position').innerHTML=Array.from({length:20},(_,i)=>`<option value="${i}">第${i+1}位</option>`).join('');
function renderPositions(){if(!cachedCharts)return;const idx=Number($('charts-position').value);$('charts-positions').innerHTML=cachedCharts.rows.slice().reverse().map(r=>{const p=r.positions[idx];return `<tr><td>${esc(r.issue)}</td><td>${p.number}</td><td>${p.tail}</td><td>${p.mod3}</td><td>${p.prime?'质':'合'}</td><td>${p.direction==='up'?'升':p.direction==='down'?'降':p.direction==='flat'?'平':'—'}</td><td>${p.amplitude??'—'}</td></tr>`}).join('');}
$('charts-position').onchange=renderPositions;
function renderChartGrid(){
 if(!cachedCharts)return;
 const mode=$('charts-grid').value,rows=cachedCharts.nineSquareLayouts[mode]||[];
 const drawn=new Set(cachedCharts.rows.at(-1)?.numbers||[]);
 $('charts-square').innerHTML=rows.flat().map(n=>`<span class="nine-cell${n!==null&&drawn.has(n)?' drawn':''}" title="${n===null?'空格':n}">${n===null?'':String(n).padStart(2,'0')}</span>`).join('');
}
async function loadCharts(){
 $('charts-status').textContent='正在读取历史统计…';
 const data=await api('/api/chart-series?limit='+encodeURIComponent($('charts-limit').value));
 cachedCharts=data;
 const rows=data.rows.slice().reverse();
 $('charts-status').textContent=`已载入${data.count}期历史数据。指标仅用于描述历史，不提供预测保证。`;
 $('charts-metrics').innerHTML=metric('分析样本',data.count,'历史期数')+metric('最新期号',rows[0]?.issue||'无')+metric('号码总出现次数',data.count*20)+metric('单号码随机期望',data.frequency.expected_frequency.toFixed(2),'仅作为比较基准');
 $('charts-history').innerHTML=rows.map(r=>`<tr><td>${esc(r.issue)}</td><td>${r.sum}</td><td>${r.span}</td><td>${r.odd}</td><td>${r.even}</td><td>${r.large}</td><td>${r.small}</td><td>${r.repeatFromPrevious??'—'}</td></tr>`).join('');
 $('charts-frequencies').innerHTML=Array.from({length:80},(_,i)=>i+1).map(n=>`<div class="number-cell"><strong>${String(n).padStart(2,'0')}</strong><small>出现 ${data.frequency.frequency[n]} · 遗漏 ${data.frequency.omission[n]}</small></div>`).join('');
 renderChartGrid();
 renderPositions();
}
$('charts-load').onclick=()=>busy('charts-load',loadCharts);
$('charts-limit').onchange=()=>loadCharts().catch(e=>message(e.message,true));
$('charts-grid').onchange=renderChartGrid;
