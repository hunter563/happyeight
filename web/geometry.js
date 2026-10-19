const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pad = n => String(n).padStart(2, '0');
const names = {geometry:'图形等权评分',square:'正方形（倾斜）',rectangle:'长方形（倾斜）',diamond:'菱形',random:'均匀随机对照'};
let result = null, selected = null, evidenceIndex = 0, loaded = false, manual = [];
$('geo-k').innerHTML = Array.from({length:10}, (_,i)=>`<option value="${i+1}" ${i===9?'selected':''}>选 ${i+1}</option>`).join('');

async function api(url, body) {
  const response = await fetch(url, body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '请求失败');
  return data;
}
async function busy(id, task) {
  const button = $(id), old = button.textContent;
  button.disabled = true; button.textContent = '处理中…';
  try { await task(); } catch(e) { $('geo-status').textContent = e.message; }
  finally { button.disabled = false; button.textContent = old; }
}
function adopt(data) {
  result = data; selected = data.rankedNumbers[0]; evidenceIndex = 0; manual = []; loaded = true;
  render();
}
async function load() {
  $('geo-status').textContent = '正在读取开奖并匹配固定图形模板…';
  const query = new URLSearchParams({k:$('geo-k').value, rows:$('geo-rows').value});
  if ($('geo-asof').value.trim()) query.set('asOfIssue',$('geo-asof').value.trim());
  adopt(await api('/api/geometry?'+query));
}
function render() {
  const r = result;
  $('geo-status').textContent = `${r.historicalReplay?'历史回放 · ':''}数据截至 ${r.asOfIssue}（${r.asOfDate}） · ${r.recordId?'已锁定记录 #'+r.recordId:'预览，尚未锁定'} · ${r.version}${r.freshness.stale?' · 数据较旧，请先更新':''}`;
  $('geo-result').innerHTML = `<div class="geo-summary"><div><small>${r.historicalReplay?'历史回放的待补行':'按库内末期推算的下一行'}</small><strong>${esc(r.targetIssue||'下一期（编号待核对）')}</strong><p>候选按号码升序显示，点击可查看图形依据。</p></div><div class="geo-candidates">${r.selections.geometry.map(n=>`<button data-candidate="${n}" aria-label="查看 ${pad(n)} 的图形依据" aria-pressed="${n===selected}">${pad(n)}<small>${r.candidates[n-1].supportCount} 图形</small></button>`).join('')}</div></div>
  <div class="geo-detail"><div id="geo-evidence-info"></div><div class="controls"><label>筛选图形<select id="geo-family"><option value="all">全部图形</option>${Object.entries(r.families).map(([key,label])=>`<option value="${key}">${esc(label)}</option>`).join('')}</select></label><label>查看匹配实例<select id="geo-evidence"></select></label></div></div>
  <div class="geo-legend"><span>● 红：历史开奖</span><span>● 蓝：当前图形已知角点</span><span>◌ 橙：下一期待补点</span><label><input type="checkbox" id="geo-manual">手动连线（最多4点）</label><button id="geo-clear">清除手动线</button></div>
  <div class="geo-chart-frame"><div id="geo-labels" class="geo-chart-labels" aria-hidden="true"></div><div id="geo-chart" class="geo-chart-scroll" tabindex="0" aria-label="走势图，可横向和纵向滚动"></div></div>
  <p class="muted" id="geo-manual-note">网格固定为正方格。可横向查看全部80个号码；下方虚线行尚未开奖。</p>
  <div class="note">${esc(r.rules.score)} ${r.unsupportedSelections.length?'无图形依据的入选号码：'+r.unsupportedSelections.map(pad).join('、')+'。':''}${r.historicalReplay?' 本页刻意隐藏截止期之后的所有开奖，属于事后历史回放。':' 图形存在不代表该号码会开出，需要按锁定记录验证。'}</div>
  <details><summary>全部80个号码的形态支持度</summary><div class="table-scroll"><table><thead><tr><th>号码</th><th>排序分数</th>${Object.values(r.families).map(n=>`<th>${esc(n)} 匹配/可用</th>`).join('')}</tr></thead><tbody>${[...r.candidates].sort((a,b)=>b.score-a.score||a.number-b.number).map(c=>`<tr><td><button data-candidate="${c.number}">${pad(c.number)}</button></td><td>${c.score.toFixed(4)}</td>${Object.values(c.families).map(f=>`<td>${f.matched} / ${f.possible}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>`;
  $('geo-result').querySelectorAll('[data-candidate]').forEach(button=>button.onclick=()=>{
    selected=Number(button.dataset.candidate); evidenceIndex=0;
    $('geo-result').querySelectorAll('.geo-candidates button').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.candidate)===selected)));
    updateEvidence();
  });
  $('geo-family').onchange=()=>{evidenceIndex=0;updateEvidence();};
  $('geo-evidence').onchange=()=>{evidenceIndex=Number($('geo-evidence').value);drawChart(true);};
  $('geo-clear').onclick=()=>{manual=[];drawChart(false);};
  updateEvidence();
}
function availableEvidence() {
  const filter=$('geo-family').value;
  return result.candidates[selected-1].evidence.filter(e=>filter==='all'||e.type===filter);
}
function updateEvidence() {
  const c=result.candidates[selected-1], list=availableEvidence();
  $('geo-evidence').innerHTML=list.length?list.map((e,i)=>`<option value="${i}">${i+1} · ${esc(names[e.type])} · 跨${-Math.min(...e.points.map(p=>p.offset))}期</option>`).join(''):'<option>没有匹配图形</option>';
  $('geo-evidence').disabled=!list.length;
  $('geo-evidence-info').innerHTML=`<b>号码 ${pad(selected)}</b> · ${c.supportCount} 个匹配图形 · 排序分数 ${c.score.toFixed(4)}<p id="geo-proof"></p>`;
  drawChart(true);
}
function drawChart(focus=false) {
  if(!result)return;
  const c=24, rows=result.chart, height=(rows.length+3)*c, width=80*c;
  const x=n=>(n-.5)*c, y=offset=>(offset+rows.length+1.5)*c;
  const text=(px,py,value,cls)=>`<text x="${px}" y="${py}" class="${cls}" text-anchor="middle" dominant-baseline="middle">${esc(value)}</text>`;
  const evidence=availableEvidence()[evidenceIndex];
  const known=new Set((evidence?.points||[]).map(p=>`${p.offset}:${p.number}`));
  let grid='', dots='', labels=text(52,12,'期号','geo-axis');
  for(let n=1;n<=80;n++){
    grid+=`<rect x="${(n-1)*c}" y="0" width="${c}" height="${height}" class="${Math.floor((n-1)/10)%2?'geo-band-b':'geo-band-a'}"/>`;
    grid+=`<path d="M ${(n-1)*c} 0 V ${height}" class="${(n-1)%10===0?'geo-zone-line':'geo-grid-line'}"/>`;
    grid+=text(x(n),12,pad(n),'geo-axis')+text(x(n),height-12,pad(n),'geo-axis');
  }
  for(const row of rows){
    const cy=y(row.offset), numbers=new Set(row.numbers);
    labels+=text(52,cy,row.issue,'geo-axis');
    grid+=`<path d="M 0 ${cy-c/2} H ${width}" class="geo-grid-line"/>`;
    for(let n=1;n<=80;n++){
      dots+=`<g data-number="${n}" data-offset="${row.offset}"><title>${esc(row.issue)}期 · ${pad(n)}${numbers.has(n)?' 已开出':' 未开出'}</title><rect x="${x(n)-12}" y="${cy-12}" width="24" height="24" fill="transparent"/>`;
      if(numbers.has(n))dots+=`<circle cx="${x(n)}" cy="${cy}" r="9.7" class="${known.has(`${row.offset}:${n}`)?'geo-known':'geo-draw'}"/>`+text(x(n),cy,pad(n),'geo-ball-text');
      else if($('geo-missing').checked)dots+=text(x(n),cy,row.missing[n-1]+(row.missingCensored.includes(n)?'+':''),'geo-missing');
      dots+='</g>';
    }
  }
  const futureY=y(0);
  labels+=text(52,futureY,result.targetIssue||'下一期','geo-future-label');
  grid+=`<rect x="0" y="${futureY-12}" width="${width}" height="24" class="geo-future-row"/>`;
  for(let n=1;n<=80;n++){
    dots+=`<g data-number="${n}" data-offset="0"><title>下一期待补 ${pad(n)}</title><rect x="${x(n)-12}" y="${futureY-12}" width="24" height="24" fill="transparent"/>`;
    if(result.selections.geometry.includes(n)||n===selected)dots+=`<circle cx="${x(n)}" cy="${futureY}" r="10" class="geo-future-dot"/>`;
    dots+=text(x(n),futureY,pad(n),n===selected?'geo-future-label':'geo-axis')+'</g>';
  }
  let lines='';
  if(evidence){
    const [a,top,b]=evidence.points;
    lines=`<path d="M ${x(a.number)} ${y(a.offset)} L ${x(top.number)} ${y(top.offset)} L ${x(b.number)} ${y(b.offset)}" class="geo-known-line"/><path d="M ${x(a.number)} ${y(a.offset)} L ${x(selected)} ${futureY} L ${x(b.number)} ${y(b.offset)}" class="geo-future-line"/>`;
    $('geo-proof').textContent=`${names[evidence.type]}：${evidence.points.map(p=>`${p.issue}期 ${pad(p.number)}`).join(' / ')} → 下一期 ${pad(selected)}（待补）`;
  }else $('geo-proof').textContent='当前筛选下没有图形依据。该号码的其他图形可切换筛选查看；零分入选仅用于固定数量比较。';
  if(manual.length) lines+=`<polyline points="${manual.map(p=>`${x(p.number)},${y(p.offset)}`).join(' ')}" class="geo-manual-line"/>`+manual.map(p=>`<circle cx="${x(p.number)}" cy="${y(p.offset)}" r="11" class="geo-manual-dot"/>`).join('');
  const el=$('geo-chart'), oldLeft=el.scrollLeft, oldTop=el.scrollTop;
  el.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" role="img" aria-label="历史开奖及几何补点走势图">${grid}${lines}${dots}</svg>`;
  $('geo-labels').innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" width="104" height="${height}">${labels}</svg>`;
  el.onscroll=()=>{$('geo-labels').scrollTop=el.scrollTop;};
  el.scrollTop=focus?Math.max(0,height-el.clientHeight):oldTop;
  el.scrollLeft=focus?Math.max(0,x(selected)-el.clientWidth/2):oldLeft;
  $('geo-labels').scrollTop=el.scrollTop;
  el.onclick=event=>{
    if(!$('geo-manual').checked)return;
    const cell=event.target.closest('[data-number]');if(!cell)return;
    if(manual.length>=4)manual=[];
    manual.push({number:Number(cell.dataset.number),offset:Number(cell.dataset.offset)});
    drawChart(false);
  };
  $('geo-manual-note').textContent=manual.length?`手动标注 ${manual.length}/4 点：${manual.map(p=>`${p.offset===0?'下一期':rows.find(r=>r.offset===p.offset).issue} / ${pad(p.number)}`).join(' → ')}。手动线仅供观察，不参与自动评分。`:'网格固定为正方格。可横向查看全部80个号码；下方虚线行尚未开奖。';
}
$('geo-load').onclick=()=>busy('geo-load',load);
$('geo-missing').onchange=()=>{if(result)drawChart(false);};
$('geo-save').onclick=()=>busy('geo-save',async()=>{
  if($('geo-asof').value.trim())throw new Error('历史回放不能保存为提前预测；请清空截止期后再锁定下一期');
  $('geo-status').textContent='正在更新最近开奖，然后生成并锁定同一份图形候选…';
  adopt(await api('/api/geometry/predict',{k:Number($('geo-k').value),rows:Number($('geo-rows').value),sync:true}));
});
$('geo-test').onclick=()=>busy('geo-test',async()=>{
  $('geo-status').textContent='正在逐期遮住目标开奖号，检验全部固定图形规则…';
  const r=await api('/api/geometry/backtest',{k:Number($('geo-k').value),folds:Number($('geo-folds').value)});
  $('geo-test-result').classList.remove('empty');
  $('geo-test-result').innerHTML=`<div class="note">${esc(r.note)}</div><p>实际 ${r.folds} 期 · 每期选 ${r.k} 个 · 理论随机平均 ${r.theoreticalMeanHits.toFixed(2)} 个 · 跳过 ${r.skipped.length} 期</p><div class="table-scroll"><table><thead><tr><th>策略</th><th>平均命中</th><th>相对理论随机</th><th>总命中</th></tr></thead><tbody>${Object.entries(r.summary).map(([key,s])=>`<tr><td>${names[key]}</td><td><b>${s.meanHits.toFixed(3)}</b></td><td>${s.deltaFromRandomExpectation>=0?'+':''}${s.deltaFromRandomExpectation.toFixed(3)}</td><td>${s.totalHits}</td></tr>`).join('')}</tbody></table></div><p class="muted">随机假设下平均命中数的近似95%范围：${r.randomNull95Band.map(n=>n.toFixed(3)).join('–')}。多组比较未经校正，不用单次高值挑选“赢家”。</p><details><summary>展开全部逐期结果</summary><div class="table-scroll"><table><thead><tr><th>目标期</th><th>数据截止</th>${Object.keys(r.summary).map(key=>`<th>${names[key]}</th>`).join('')}</tr></thead><tbody>${[...r.records].reverse().map(row=>`<tr><td>${row.issue}</td><td>${row.trainThrough}</td>${Object.keys(r.summary).map(key=>`<td>${row.hits[key]} / ${r.k}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>`;
  $('geo-status').textContent='图形回测完成，结果见下方。回测不会保存为开奖前预测。';
});
function enter(){if(location.hash==='#geometry'&&!loaded)busy('geo-load',load);}
window.addEventListener('hashchange',enter);enter();
