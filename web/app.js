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
let chartReplayTimer=null, chartReplayIndex=null, heatmapInstance=null;
$('charts-track-number').innerHTML='<option value="0">全部号码</option>'+Array.from({length:80},(_,i)=>'<option value="'+(i+1)+'">'+String(i+1).padStart(2,'0')+'号</option>').join('');
function stopChartReplay(){
 if(chartReplayTimer!==null){clearInterval(chartReplayTimer);chartReplayTimer=null;}
 $('charts-replay-toggle').textContent='▶ 历史回放';
}
function renderHeatmap(){
 if(!cachedCharts)return;
 const rows=cachedCharts.rows, end=chartReplayIndex===null?rows.length-1:chartReplayIndex;
 const selected=Number($('charts-track-number').value);
 const div=$('charts-heatmap');
 if(!globalThis.echarts){div.textContent='热力图需要加载 ECharts，请确认网络或部署资源。';return;}
 if(!heatmapInstance)heatmapInstance=echarts.init(div,null,{renderer:'canvas'});
 const shown=rows.slice(0,end+1),data=[];
 shown.forEach((r,i)=>{const found=new Set(r.numbers);for(let n=1;n<=80;n++){const hit=found.has(n);data.push([n-1,i,hit?(selected&&selected!==n?2:1):0]);}});
 heatmapInstance.setOption({
  animation:shown.length<=50,
  grid:{left:72,right:28,top:30,bottom:52},
  tooltip:{position:'top',formatter:({data:d})=>{const row=shown[d[1]];return '第 '+esc(row.issue)+' 期 · '+(d[0]+1)+'号：'+(d[2]===0?'未出现': '出现');}},
  xAxis:{type:'category',data:Array.from({length:80},(_,i)=>String(i+1).padStart(2,'0')),axisLabel:{interval:7},splitArea:{show:false}},
  yAxis:{type:'category',data:shown.map(r=>r.issue),axisLabel:{hideOverlap:true}},
  visualMap:{show:false,type:'piecewise',pieces:[{value:0,color:'#f1f3ee'},{value:1,color:'#d6542c'},{value:2,color:'#d1d7d4'}]},
  dataZoom:[{type:'inside',xAxisIndex:0,start:0,end:100},{type:'inside',yAxisIndex:0,start:Math.max(0,100-45/Math.max(1,shown.length)*100),end:100}],
  series:[{type:'heatmap',data,progressive:4000,emphasis:{itemStyle:{borderColor:'#184758',borderWidth:1}}}]
 },true);
 heatmapInstance.resize();
 const status=$('charts-replay-status');
 status.textContent='展示至第 '+(rows[end]?.issue||'—')+' 期；红色为当期出现，灰色为其他已出现号码。';
 if(rows[end]){const appeared=new Set(rows[end].numbers);$('charts-square').querySelectorAll('.nine-cell').forEach(e=>{const n=Number(e.textContent);e.classList.toggle('drawn',n>0&&appeared.has(n));});}
}
$('charts-track-number').onchange=renderHeatmap;
$('charts-replay-toggle').onclick=()=>{
 if(!cachedCharts)return;
 if(chartReplayTimer!==null){stopChartReplay();return;}
 const rows=cachedCharts.rows;if(!rows.length)return;
 if(chartReplayIndex===null||chartReplayIndex>=rows.length-1)chartReplayIndex=0;
 $('charts-replay-toggle').textContent='Ⅱ 暂停';
 chartReplayTimer=setInterval(()=>{
  if(chartReplayIndex>=rows.length-1){stopChartReplay();return;}
  chartReplayIndex++;renderHeatmap();
 },Number($('charts-replay-speed').value));
 renderHeatmap();
 chartFamilySelection();
};
$('charts-replay-reset').onclick=()=>{stopChartReplay();chartReplayIndex=null;renderHeatmap()};
$('charts-replay-speed').onchange=()=>{if(chartReplayTimer!==null){stopChartReplay();$('charts-replay-toggle').click();}};
window.addEventListener('resize',()=>heatmapInstance?.resize());

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
 stopChartReplay();chartReplayIndex=null;
 cachedCharts=data;
 const rows=data.rows.slice().reverse();
 $('charts-status').textContent=`已载入${data.count}期历史数据。指标仅用于描述历史，不提供预测保证。`;
 $('charts-metrics').innerHTML=metric('分析样本',data.count,'历史期数')+metric('最新期号',rows[0]?.issue||'无')+metric('号码总出现次数',data.count*20)+metric('单号码随机期望',data.frequency.expected_frequency.toFixed(2),'仅作为比较基准');
 $('charts-history').innerHTML=rows.map(r=>`<tr><td>${esc(r.issue)}</td><td>${r.sum}</td><td>${r.span}</td><td>${r.odd}</td><td>${r.even}</td><td>${r.large}</td><td>${r.small}</td><td>${r.repeatFromPrevious??'—'}</td><td>${r.trend.overlapKnown?r.trend.adjacent:'—'}</td><td>${r.trend.overlapKnown?r.trend.adjacentNew:'—'}</td><td>${r.trend.decadeDistribution.join(' / ')}</td></tr>`).join('');
 $('charts-frequencies').innerHTML=Array.from({length:80},(_,i)=>i+1).map(n=>`<div class="number-cell"><strong>${String(n).padStart(2,'0')}</strong><small>出现 ${data.frequency.frequency[n]} · 遗漏 ${data.frequency.omission[n]} · 连出 ${data.streakSummary[n].currentRun}</small></div>`).join('');
 renderChartGrid();
 renderPositions();
 renderTrendLine();
 renderHeatmap();
}
$('charts-load').onclick=()=>busy('charts-load',loadCharts);
$('charts-limit').onchange=()=>loadCharts().catch(e=>message(e.message,true));
$('charts-grid').onchange=renderChartGrid;

const chartLabel={sum:'和值',span:'跨度',odd:'奇数个数',repeatFromPrevious:'重号个数',consecutivePairs:'连号对数'};
let echartsTrendInstance=null;
function renderEchartsTrendLine(){
 if(!cachedCharts || !globalThis.echarts)return false;
 const chartEl=$('charts-line'),tooltip=$('charts-line-tooltip');
 if(!echartsTrendInstance)echartsTrendInstance=echarts.init(chartEl,null,{renderer:'canvas'});
 const key=$('charts-line-metric').value;
 const rows=cachedCharts.rows;
 const left=Math.min(Number($('charts-range-from').value),Number($('charts-range-to').value));
 const right=Math.max(Number($('charts-range-from').value),Number($('charts-range-to').value));
 const lo=Math.floor((rows.length-1)*left/100);
 const hi=Math.ceil((rows.length-1)*right/100);
 const visible=rows.slice(lo,hi+1);
 const values=visible.map(r=>Number.isFinite(r[key])?r[key]:null);
 echartsTrendInstance.setOption({
  animation:true,animationDuration:480,animationDurationUpdate:260,
  backgroundColor:'transparent',
  grid:{left:55,right:28,top:24,bottom:55},
  tooltip:{trigger:'axis',axisPointer:{type:'cross',snap:true},
   formatter:items=>{const d=visible[items?.[0]?.dataIndex];return d?'第 '+esc(d.issue)+' 期<br/>'+esc(chartLabel[key])+'：'+(d[key]??'暂无'):''}},
  toolbox:{right:6,top:0,feature:{saveAsImage:{title:'保存走势图',pixelRatio:2},restore:{title:'恢复缩放'}}},
  xAxis:{type:'category',boundaryGap:false,data:visible.map(r=>r.issue),axisLabel:{hideOverlap:true},axisLine:{lineStyle:{color:'#aeb6b3'}}},
  yAxis:{type:'value',scale:true,splitLine:{lineStyle:{color:'#e4e8e5'}}},
  dataZoom:[{type:'inside',start:0,end:100,zoomOnMouseWheel:true,moveOnMouseMove:false},
            {type:'slider',start:0,end:100,bottom:3,height:20}],
  series:[{name:chartLabel[key],type:'line',data:values,connectNulls:false,
           smooth:false,symbol:'circle',symbolSize:6,
           showSymbol:$('charts-line-points').checked,
           lineStyle:{width:2.5,color:'#d6542c'},
           itemStyle:{color:'#d6542c'},areaStyle:{opacity:.045,color:'#d6542c'}}]
 },true);
 echartsTrendInstance.off('updateAxisPointer');
 echartsTrendInstance.on('updateAxisPointer',e=>{
  const index=e.axesInfo?.[0]?.value;
  const row=Number.isInteger(index)?visible[index]:null;
  tooltip.textContent=row?'第 '+row.issue+' 期 · '+chartLabel[key]+'：'+(row[key]??'无数据'):'';
 });
 echartsTrendInstance.resize();
 return true;
}
window.addEventListener('resize',()=>echartsTrendInstance?.resize());
function renderTrendLine(){
 if(!cachedCharts)return;
 if(renderEchartsTrendLine())return;
 if(echartsTrendInstance){echartsTrendInstance.dispose();echartsTrendInstance=null;}
 const metricName=$('charts-line-metric').value;
 const all=cachedCharts.rows;
 const fromPercent=Number($('charts-range-from').value);
 const toPercent=Number($('charts-range-to').value);
 const from=Math.floor((all.length-1)*Math.min(fromPercent,toPercent)/100);
 const to=Math.ceil((all.length-1)*Math.max(fromPercent,toPercent)/100);
 const shown=all.slice(from,to+1);
 const values=shown.map(r=>r[metricName]);
 const finite=values.filter(n=>typeof n==='number'&&Number.isFinite(n));
 const div=$('charts-line'),tooltip=$('charts-line-tooltip');
 if(!finite.length){div.textContent='该范围暂无有效数据';tooltip.textContent='';return;}
 const W=1000,H=305,L=55,R=22,T=24,B=52,inner=W-L-R,height=H-T-B;
 const lo=Math.min(...finite),hi=Math.max(...finite);
 const delta=Math.max(1,hi-lo),bottom=lo-delta*.1,top=hi+delta*.1;
 const x=i=>L+(shown.length===1?inner/2:i*inner/(shown.length-1));
 const y=v=>T+(top-v)/(top-bottom)*height;
 let runs=[],run=[];
 shown.forEach((row,i)=>{const val=row[metricName];if(typeof val==='number'&&Number.isFinite(val))run.push([i,val]);else if(run.length){runs.push(run);run=[];}});
 if(run.length)runs.push(run);
 const polylines=runs.map(part=>'<polyline points="'+part.map(([i,v])=>x(i).toFixed(2)+','+y(v).toFixed(2)).join(' ')+'" fill="none" stroke="#d6542c" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>').join('');
 const ticks=Array.from({length:5},(_,i)=>{const val=bottom+(top-bottom)*i/4;const yy=y(val);return '<line x1="'+L+'" y1="'+yy+'" x2="'+(W-R)+'" y2="'+yy+'" stroke="#e6e8e3"/><text x="'+(L-8)+'" y="'+(yy+4)+'" text-anchor="end" fill="#65747a" font-size="12">'+val.toFixed(1)+'</text>'}).join('');
 const points=$('charts-line-points').checked?shown.map((row,i)=>typeof row[metricName]==='number'?'<circle cx="'+x(i)+'" cy="'+y(row[metricName])+'" r="3.6" fill="#d6542c"/>':'').join(''):'';
 div.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="xMidYMid meet" aria-label="'+chartLabel[metricName]+'历史折线">'+ticks+polylines+points+'<line x1="'+L+'" y1="'+(H-B)+'" x2="'+(W-R)+'" y2="'+(H-B)+'" stroke="#89959b"/><text x="'+L+'" y="'+(H-18)+'" font-size="12">'+esc(shown[0]?.issue||'')+'</text><text x="'+(W-R)+'" y="'+(H-18)+'" text-anchor="end" font-size="12">'+esc(shown.at(-1)?.issue||'')+'</text><line id="chart-crosshair" x1="'+L+'" y1="'+T+'" x2="'+L+'" y2="'+(H-B)+'" stroke="#376b75" stroke-dasharray="4 4" visibility="hidden"/><rect x="'+L+'" y="'+T+'" width="'+inner+'" height="'+height+'" fill="transparent" id="chart-hotzone"/></svg>';
 const zone=div.querySelector('#chart-hotzone'),cross=div.querySelector('#chart-crosshair');
 zone.addEventListener('pointermove',event=>{const svg=zone.ownerSVGElement,box=svg.getBoundingClientRect();const xpos=(event.clientX-box.left)*W/box.width;const i=shown.length===1?0:Math.max(0,Math.min(shown.length-1,Math.round((xpos-L)*(shown.length-1)/inner)));const row=shown[i];cross.setAttribute('x1',x(i));cross.setAttribute('x2',x(i));cross.setAttribute('visibility','visible');tooltip.textContent='第 '+row.issue+' 期 · '+chartLabel[metricName]+'：'+(row[metricName]??'无数据')});
 zone.addEventListener('pointerleave',()=>{cross.setAttribute('visibility','hidden');tooltip.textContent='';});
}
$('charts-line-metric').onchange=renderTrendLine;
$('charts-line-points').onchange=renderTrendLine;
$('charts-range-from').oninput=renderTrendLine;
$('charts-range-to').oninput=renderTrendLine;
$('charts-line-reset').onclick=()=>{$('charts-range-from').value=0;$('charts-range-to').value=100;renderTrendLine()};

const chartCatalog={
 position:Array.from({length:20},(_,i)=>({id:String(i),title:'第'+(i+1)+'位号码走势'})),
 special:[['element','五行'],['color','波色'],['sum81','和81码分区'],['has_digit','包含数字0—9'],['double','对子号'],['reverse','对望码'],['neither','非对非望']].map(([id,title])=>({id,title})),
 residue:Array.from({length:18},(_,i)=>({id:String(i+3),title:(i+3)+'余数分布'})),
 range:Array.from({length:10},(_,i)=>({id:String(i+3),title:(i+3)+'等宽区间分布'})),
 scalar:[['sum','和值'],['sumTail','和值尾数'],['span','跨度'],['spanTail','跨度尾数'],['mean','平均值'],['max','最大号'],['min','最小号'],['odd','奇数个数'],['even','偶数个数'],['prime','质数个数'],['composite','合数个数'],['small','小号个数'],['large','大号个数'],['sumSpanSumTail','和跨和尾'],['sumSpanDiffTail','和跨差尾'],['consecutivePairs','连号对数']].map(([id,title])=>({id,title}))
};
let chartFamilyInstance=null;
function chartFamilySelection(){
 const family=$('charts-family').value;
 $('charts-family-item').innerHTML=chartCatalog[family].map(x=>'<option value="'+esc(x.id)+'">'+esc(x.title)+'</option>').join('');
 renderChartFamily();
}
function renderChartFamily(){
 if(!cachedCharts)return;
 const holder=$('charts-family-view'),desc=$('charts-family-description');
 const family=$('charts-family').value,id=$('charts-family-item').value;
 if(!id)return;
 const rows=cachedCharts.rows;
 let groups=[],series=[],legend=[];
 if(family==='position'){
   const idx=Number(id);
   series=[{name:'第'+(idx+1)+'位',type:'line',data:rows.map(r=>r.positions[idx].number),smooth:false,showSymbol:false}];
   desc.textContent='依据升序排列的第'+(idx+1)+'个开奖号，纵轴显示实际号码，支持悬停与缩放。';
 }else if(family==='special'){
   const prefixes={element:['element_'],color:['color_'],sum81:['sum81_'],has_digit:['has_digit_']};
   const selected=(prefixes[id]?Object.keys(rows[0]?.special||{}).filter(k=>prefixes[id].some(p=>k.startsWith(p))):[id]);
   series=selected.map(k=>({name:k.replace('element_','五行 ').replace('color_','波色 ').replace('sum81_','和81组 ').replace('has_digit_','含数字 '),type:'line',showSymbol:false,data:rows.map(r=>r.special?.[k]??null)}));
   desc.textContent='公开数学分类的独立统计实现：'+(chartCatalog.special.find(x=>x.id===id)?.title||id)+'。特殊分类可能有交叉，请勿将各组数量简单相加。';
 }else if(family==='scalar'){
   const name=chartCatalog.scalar.find(x=>x.id===id)?.title||id;
   series=[{name,type:'line',data:rows.map(r=>r[id]??null),smooth:false,showSymbol:false}];
   desc.textContent='独立计算的历史指标：'+name+'。仅统计过去，不推断未来。';
 }else{
   const modulus=Number(id);
   groups=Array.from({length:modulus},(_,i)=>i);
   series=groups.map(i=>({
      name:family==='residue'?'余'+i:'区间'+(i+1),
      type:'line',
      data:rows.map(r=>family==='residue'?r.residues[id]?.[i]??null:r.ranges[id]?.[i]??null),
      smooth:false,showSymbol:false
   }));
   desc.textContent=family==='residue'?'按号码对'+id+'取余（余0至余'+(modulus-1)+'）分组，纵轴为每期开奖个数。':'按1—80顺序划分成'+id+'个尽可能等宽的区间，纵轴为每期开奖个数；这属于独立定义，并非所有原站区间设置。';
 }
 if(!globalThis.echarts){holder.textContent='此图需要 ECharts，请检查静态资源加载。';return;}
 if(!chartFamilyInstance)chartFamilyInstance=echarts.init(holder,null,{renderer:'canvas'});
 chartFamilyInstance.setOption({
   animationDuration:350,
   color:['#d6542c','#247f99','#57966f','#9555a4','#b28b39','#2d5669','#b65770','#6b8d3d'],
   tooltip:{trigger:'axis',axisPointer:{type:'cross'}},
   legend:{type:'scroll',top:3,show:series.length>1},
   toolbox:{feature:{saveAsImage:{title:'保存图表'},restore:{title:'复原'}}},
   grid:{left:48,right:20,top:series.length>1?50:34,bottom:62},
   xAxis:{type:'category',data:rows.map(r=>r.issue),axisLabel:{hideOverlap:true}},
   yAxis:{type:'value',scale:family==='position',min:family==='position'?1:0},
   dataZoom:[{type:'inside',start:Math.max(0,100-50/Math.max(1,rows.length)*100),end:100},{type:'slider',bottom:10,height:20}],
   series
 },true);
 chartFamilyInstance.resize();
}
$('charts-family').onchange=chartFamilySelection;
$('charts-family-item').onchange=renderChartFamily;
window.addEventListener('resize',()=>chartFamilyInstance?.resize());
