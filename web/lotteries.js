/* Eight-game historical UI; no dependency on the frozen prediction UI. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const state = {game:'kl8', field:'primary', version:'current', view:'distribution', data:null, catalog:[], request:0, controller:null, writing:false};
  const fmt = (n, spec) => spec.min === 0 ? String(n) : String(n).padStart(2, '0');

  async function api(path, options={}) {
    const response = await fetch(path, options);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `请求失败（${response.status}）`);
    return result;
  }
  function notice(message='') { $('message').textContent = message; }
  function ruleText(game) {
    const p = game.primary;
    const first = `${p.label} ${p.min}—${p.max} · ${p.count}个${p.ordered ? '有序数字，允许重复' : '不重复号码'}`;
    const s = game.secondary;
    return first + (s ? ` / ${s.label} ${s.min}—${s.max} · ${s.count}个` : '');
  }
  function balls(draw, game) {
    if (!draw) return '';
    const render = (values, spec, extra='') => values.map(n => `<span class="ball ${extra}">${fmt(n,spec)}</span>`).join('');
    return render(draw.primary, game.primary) + (draw.secondary.length ? '<span class="ball-divider">/</span>' + render(draw.secondary, game.secondary, 'secondary') : '');
  }
  function renderCatalog() {
    $('games').innerHTML = state.catalog.map(game => `<button type="button" data-game="${game.id}" class="${state.game===game.id?'active':''}" aria-pressed="${state.game===game.id}" ${state.writing?'disabled':''}><span>${esc(game.name)}</span><small>${esc(game.issuer)}</small></button>`).join('');
  }
  async function refreshCatalog() {
    state.catalog = (await api('/api/lotteries')).games;
    renderCatalog();
  }
  function prepareGame() {
    const spec = state.catalog.find(g => g.id===state.game);
    $('game-title').textContent = spec.name;
    $('game-rule').textContent = ruleText(spec);
    $('latest-issue').textContent = '—';
    $('latest-balls').replaceChildren();
    $('latest-source').textContent = '读取库内记录…';
    $('total').textContent = '—'; $('window-count').textContent = '—';
    $('freshness').textContent = '正在读取'; $('window-range').textContent = '—';
    $('version-label').hidden = state.game !== 'qxc';
    $('version').value = state.version;
    $('field').innerHTML = `<option value="primary">${esc(spec.primary.label)}</option>`;
    $('export').href = `/api/lotteries/${state.game}/export`;
    $('sync').hidden = state.game !== 'kl8';
    $('format-note').textContent = `${spec.name}：${ruleText(spec)}。` + (spec.secondary ? '两个号码区必须分别填写primary与secondary。' : 'secondary留空。') + (spec.primary.ordered ? '可填写001等紧凑数字文本，保留首位0。' : '') + (state.game==='qlc'?'特别号不能与基本号重复。':'');
    $('import-status').textContent = '';
  }
  async function selectGame(game) {
    if (state.writing || !state.catalog.some(g => g.id===game)) return;
    state.game = game; state.field = 'primary'; state.version='current'; state.data=null;
    $('from').value=''; $('to').value='';
    history.replaceState(null, '', `#${game}`);
    renderCatalog(); prepareGame(); await load();
  }
  async function load() {
    const token = ++state.request;
    if (state.controller) state.controller.abort();
    state.controller = new AbortController();
    document.body.classList.add('loading');
    $('workspace-status')?.remove();
    $('analysis').hidden = true; $('empty').hidden = true;
    notice('');
    const params = new URLSearchParams({limit:$('limit').value, version:state.version, field:state.field});
    for (const key of ['from','to']) if ($(key).value.trim()) params.set(key,$(key).value.trim());
    try {
      const result = await api(`/api/lotteries/${state.game}?${params}`, {signal:state.controller.signal});
      if (token!==state.request) return;
      state.data = result;
      render();
    } catch (error) {
      if (error.name!=='AbortError' && token===state.request) {
        state.data=null;
        notice(`载入失败：${error.message}。请调整范围或刷新重试。`);
        $('latest-balls').replaceChildren(); $('latest-issue').textContent='—';
        $('latest-source').textContent='载入失败'; $('window-count').textContent='—'; $('window-range').textContent='—';
      }
    } finally {
      if (token===state.request) document.body.classList.remove('loading');
    }
  }
  function render() {
    const data = state.data, spec=data.game;
    $('game-rule').textContent = ruleText(spec);
    $('total').textContent = data.totalStored.toLocaleString('zh-CN');
    $('window-count').textContent = data.count;
    $('window-range').textContent = data.count ? `${data.fromIssue} — ${data.toIssue}` : '没有符合条件的记录';
    $('freshness').textContent = data.latest ? `窗口末期距今 ${data.ageDays} 天` : (data.totalStored ? '当前规则或范围没有记录' : '待导入真实开奖');
    $('latest-issue').textContent = data.latest ? `${data.latest.issue} 期 · ${data.latest.date}` : '暂无记录';
    $('latest-balls').innerHTML = balls(data.latest, spec);
    $('latest-source').textContent = data.latest ? `来源：${data.latest.source}` : '未接入或未导入数据，不显示模拟开奖结果。';
    $('definitions').textContent = data.definition;
    $('field').innerHTML = data.fields.map(f => `<option value="${f.id}" ${f.id===state.field?'selected':''}>${esc(f.label)}</option>`).join('');
    $('field-badge').textContent = data.activeField.label;
    $('empty').hidden = data.count>0;
    $('analysis').hidden = !data.count;
    if (!data.count) {
      $('empty-title').textContent = data.totalStored ? '当前条件没有匹配的开奖' : `${spec.name}还没有入库数据`;
      $('empty-text').textContent = data.totalStored ? '可清空期号范围；七星彩也可以切换新旧规则。' : '数据校验和分析功能已经就绪。导入真实开奖文件后，即可查看走势。';
    }
    $('metric').querySelector('[value="amplitude"]').disabled = data.activeField.spec.count!==1;
    if ($('metric').value==='amplitude' && data.activeField.spec.count!==1) $('metric').value='sum';
    renderView();
  }
  function rowsInOrder(rows) { return $('order').value==='desc' ? [...rows].reverse() : rows; }
  function renderView() {
    document.querySelectorAll('[data-view]').forEach(button => {
      const active = button.dataset.view===state.view;
      button.classList.toggle('active',active); button.setAttribute('aria-pressed',String(active));
    });
    for (const id of ['distribution','frequency','trend','history']) $(id).hidden=id!==state.view;
    if (!state.data?.count) return;
    if (state.view==='distribution') renderDistribution();
    if (state.view==='frequency') renderFrequency();
    if (state.view==='trend') renderTrend();
    if (state.view==='history') renderHistory();
  }
  function renderDistribution() {
    const field=state.data.activeField, spec=field.spec;
    const numbers = field.frequencies.map(f=>f.number);
    const head=`<thead><tr><th>期号</th>${numbers.map(n=>`<th>${fmt(n,spec)}</th>`).join('')}<th>和值</th><th>跨度</th></tr></thead>`;
    const body=rowsInOrder(field.series).map(row=>{
      const counts = new Map(); for (const n of row.values) counts.set(n,(counts.get(n)||0)+1);
      return `<tr><td>${row.issue}</td>${row.omissions.map(cell=>{
        const n=cell.number, count=counts.get(n);
        return count ? `<td><span class="hit ${count>1?'multi':''}" title="${row.issue}期 · ${fmt(n,spec)}出现${count}次">${fmt(n,spec)}${count>1?`×${count}`:''}</span></td>` : `<td><span class="miss" title="截至本期，库内遗漏${cell.lowerBound?'至少':''}${cell.value}条记录">${cell.lowerBound?'≥':''}${cell.value}</span></td>`;
      }).join('')}<td class="stat">${row.sum}</td><td class="stat">${row.span}</td></tr>`;
    }).join('');
    $('distribution-table').innerHTML=head+`<tbody>${body}</tbody>`;
    $('distribution-table').classList.toggle('hide-omissions',!$('omissions').checked);
  }
  function renderFrequency() {
    const field=state.data.activeField, sort=$('frequency-sort').value;
    const values=[...field.frequencies].sort((a,b)=> sort==='number' ? a.number-b.number : b[sort]-a[sort] || a.number-b.number);
    const max=Math.max(1,...values.map(v=>v.count));
    $('frequency-grid').innerHTML=values.map(v=>`<article class="frequency-card"><strong>${fmt(v.number,field.spec)}</strong><meter min="0" max="${max}" value="${v.count}" aria-label="出现${v.count}次"></meter><p>出现次数<b>${v.count}</b></p><p>出现期数<b>${v.drawCount}</b></p><p>当前遗漏<b>${v.lowerBound?'≥':''}${v.omission}</b></p></article>`).join('');
  }
  function renderTrend() {
    const field=state.data.activeField, metric=$('metric').value, series=field.series;
    const values=series.map(r=>r[metric]).filter(v=>v!==null), min=Math.min(...values), max=Math.max(...values);
    if (!values.length) {
      $('line-chart').textContent='缺少此前记录，无法计算这个指标。';
      $('line-summary').textContent='';
    } else {
      const lo=min===max ? Math.max(0,min-1) : min, hi=max===lo ? lo+1 : max;
      const x=i=>50+i*810/Math.max(1,series.length-1), y=v=>208-(v-lo)*180/(hi-lo);
      const segments=[];let path='';
      series.forEach((r,i)=>{ if (r[metric]===null) {if(path)segments.push(path);path='';} else {path+=`${path?'L':'M'}${x(i).toFixed(2)},${y(r[metric]).toFixed(2)} `;} });
      if(path) segments.push(path);
      const title=$('metric').selectedOptions[0].textContent;
      const ticks=Array.from({length:4},(_,i)=>lo+(hi-lo)*i/3);
      $('line-chart').innerHTML=`<svg viewBox="0 0 900 250" role="img" aria-labelledby="trend-title trend-desc"><title id="trend-title">${esc(field.label)} · ${esc(title)}</title><desc id="trend-desc">${series.length}条库内记录，最小${min}，最大${max}。详细数字见下表。</desc>${ticks.map(v=>`<line class="chart-grid" x1="50" x2="860" y1="${y(v)}" y2="${y(v)}"/><text class="chart-axis" x="40" y="${y(v)+3}" text-anchor="end">${Number(v.toFixed(1))}</text>`).join('')}${segments.map(d=>`<path class="chart-line" d="${d}"/>`).join('')}${series.filter(r=>r[metric]!==null).map(r=>{const i=series.indexOf(r);return `<circle class="chart-point" cx="${x(i)}" cy="${y(r[metric])}" r="${series.length>100?2:3}"><title>${r.issue}期：${r[metric]}</title></circle>`;}).join('')}<text class="chart-axis" x="50" y="236">${series[0].issue}</text><text class="chart-axis" x="860" y="236" text-anchor="end">${series.at(-1).issue}</text></svg>`;
      $('line-summary').textContent=`${title} · 最小 ${min} / 最大 ${max} / 均值 ${(values.reduce((a,b)=>a+b,0)/values.length).toFixed(2)}。大号定义：${Math.floor((field.spec.min+field.spec.max+1)/2)}—${field.spec.max}（全号池口径）；012路按号码除以3的余数分类。`;
    }
    $('metrics-body').innerHTML=rowsInOrder(series).map(r=>`<tr><td>${r.issue}</td><td>${r.sum}</td><td>${r.span}</td><td>${r.odd} : ${r.values.length-r.odd}</td><td>${r.big} : ${r.values.length-r.big}</td><td>${r.residues.join(' : ')}</td><td>${r.repeat??'—'}</td><td>${r.amplitude??'—'}</td></tr>`).join('');
  }
  function renderHistory() {
    $('history-body').innerHTML=rowsInOrder(state.data.draws).map(row=>`<tr><td>${row.issue}</td><td>${row.date}</td><td><div class="balls">${balls(row,state.data.game)}</div></td><td>${esc(row.source)}</td></tr>`).join('');
  }
  function writing(value) {
    state.writing=value;
    $('import-file').disabled=value; $('sync').disabled=value;
    renderCatalog();
  }
  async function importFile(file) {
    if (!file) return;
    const game=state.game, name=state.catalog.find(g=>g.id===game).name;
    writing(true); $('import-status').textContent=`正在校验并导入${name}…`;
    try {
      if (file.size>1_900_000) throw new Error('文件过大，请拆分为小于1.9MB的文件');
      const text=await file.text(); let body;
      if (file.name.toLowerCase().endsWith('.csv')) body={csv:text};
      else if (file.name.toLowerCase().endsWith('.json')) {
        const parsed=JSON.parse(text);
        body=Array.isArray(parsed)?{draws:parsed}:parsed;
        if (!body || typeof body!=='object' || !Array.isArray(body.draws)) throw new Error('JSON须为记录数组，或包含draws数组的对象');
        body={game:body.game??game,draws:body.draws};
      } else throw new Error('仅支持CSV或JSON文件');
      body.source=$('source').value.trim();
      const encoded=JSON.stringify(body);
      if(new TextEncoder().encode(encoded).length>2_000_000) throw new Error('编码后超过2MB，请拆分文件');
      const result=await api(`/api/lotteries/${game}/import`,{method:'POST',headers:{'Content-Type':'application/json'},body:encoded});
      $('import-status').textContent=`${name}：新增${result.inserted}期，跳过${result.duplicates}条重复记录。`;
      await refreshCatalog(); await load();
    } catch(error) { $('import-status').textContent=`导入失败：${error.message}`; }
    finally {writing(false); $('import-file').value='';}
  }
  $('games').addEventListener('click',event=>{const button=event.target.closest('[data-game]');if(button)selectGame(button.dataset.game);});
  document.querySelector('.tabs').addEventListener('click',event=>{const button=event.target.closest('[data-view]');if(button){state.view=button.dataset.view;renderView();}});
  $('filters').addEventListener('submit',event=>{event.preventDefault();load();});
  $('limit').addEventListener('change',load);
  $('field').addEventListener('change',()=>{state.field=$('field').value;load();});
  $('version').addEventListener('change',()=>{state.version=$('version').value;load();});
  $('reload').addEventListener('click',async()=>{try{await refreshCatalog();await load();}catch(error){notice(error.message);}});
  $('omissions').addEventListener('change',()=> $('distribution-table').classList.toggle('hide-omissions',!$('omissions').checked));
  $('order').addEventListener('change',renderView);
  $('frequency-sort').addEventListener('change',()=>{if(state.data?.count)renderFrequency();});
  $('metric').addEventListener('change',()=>{if(state.data?.count)renderTrend();});
  $('open-import').addEventListener('click',()=>{$('data-workspace').open=true;$('data-workspace').scrollIntoView({behavior:'smooth',block:'start'});$('source').focus({preventScroll:true});});
  $('import-file').addEventListener('change',()=>importFile($('import-file').files[0]));
  $('sync').addEventListener('click',async()=>{
    writing(true);$('import-status').textContent='正在同步快乐8…';
    try {const r=await api('/api/sync',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});$('import-status').textContent=`新增${r.inserted}期，跳过${r.duplicates}条重复记录。`;await refreshCatalog();await load();}
    catch(error){$('import-status').textContent=`同步失败：${error.message}。保留原有数据。`;}
    finally {writing(false);}
  });
  window.addEventListener('hashchange',()=>selectGame(location.hash.slice(1)));
  refreshCatalog().then(()=>selectGame(state.catalog.some(g=>g.id===location.hash.slice(1))?location.hash.slice(1):'kl8')).catch(error=>notice(`初始化失败：${error.message}。请刷新页面重试。`));
})();
