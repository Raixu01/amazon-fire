'use strict';
const $ = id => document.getElementById(id);
const M = FireModel, DAY = M.dayMs;
const nf = new Intl.NumberFormat('pt-BR', {maximumFractionDigits:1});
const fmt = n => n == null || !Number.isFinite(n) ? 'Indisponível' : nf.format(n);
const date = stamp => stamp ? new Intl.DateTimeFormat('pt-BR',{timeZone:'America/Sao_Paulo',dateStyle:'short',timeStyle:'short'}).format(new Date(stamp)) : 'Indisponível';
const esc = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const months = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
const state = {mode:'recent',recent:{days:7,uf:'',search:'',view:'points'},history:{year:null,month:0,uf:'',search:'',metric:'total'}};
let geo, municipalities, map, mapLayer, pointLayer, history, historyMeta, recentMeta, sequence=0, animation=null, firstMap=true;
let lastTotals = new Map(), lastFeatures=[], lastMetric=new Map();
let visiblePointRows=[], selectedCode=null, historyScale=1;
const cache = new Map();
function notice(text, kind='') { $('status').textContent=text; $('status').className='notice '+kind; }
async function json(url, compressed=false) {
  const response = await fetch(url, {cache: compressed ? 'default' : 'no-store'});
  if(!response.ok) throw new Error('Não foi possível carregar '+url+' ('+response.status+').');
  if(!compressed) return response.json();
  const bytes = new Uint8Array(await response.arrayBuffer());
  const text = new TextDecoder().decode(bytes[0]===31 && bytes[1]===139 ? pako.ungzip(bytes) : bytes);
  return JSON.parse(text);
}
function blob(path) {
  if(!cache.has(path)) cache.set(path, json('data/'+path,true).catch(error=>{cache.delete(path);throw error;}));
  return cache.get(path);
}
function subset() {
  const filter=state[state.mode], query=fold(filter.search);
  return geo.features.filter(f=>(!selectedCode || f.properties.codigo_ibge===selectedCode) && (!filter.uf || f.properties.uf===filter.uf) && (!query || fold(f.properties.nome).includes(query)));
}
function mCode(m){return String(m.codigo_ibge);}
function fold(s) { return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }
function syncControls() {
  const h=state.mode==='history', filter=state[state.mode];
  document.body.dataset.mode=state.mode;
  $('recent-filters').hidden=h; $('history-filters').hidden=!h; $('view-label').hidden=h; $('metric-label').hidden=!h;
  $('history-experience').hidden=!h; $('comparison').hidden=!h; $('play').hidden=!h;
  for(const [id,active] of [['nav-recent',!h],['nav-history',h]]) {
    $(id).classList.toggle('active',active);
    if(active) $(id).setAttribute('aria-current','page'); else $(id).removeAttribute('aria-current');
  }
  $('eyebrow').textContent=h?'ENTENDA A EVOLUÇÃO':'ACOMPANHE O PRESENTE';
  $('title').textContent=h?'Análise histórica':'Monitoramento recente';
  $('description').textContent=h?'Como os focos mudaram ao longo do tempo? Compare anos e meses da série de referência.':'Onde estão os focos nos últimos dias? Explore o mapa e acompanhe a evolução dos registros.';
  $('intro-note').innerHTML=h?'Uma série comparável<br><strong>Somente anos completos · satélite de referência</strong>':'Atualização automática<br><strong>Conforme disponibilidade do INPE</strong>';
  $('state').value=filter.uf; $('search').value=filter.search;
  $('year').value=state.history.year; $('month').value=state.history.month;
  $('metric').value=state.history.metric; $('view').value=state.recent.view;
  document.querySelectorAll('[data-days]').forEach(b=>{const on=Number(b.dataset.days)===state.recent.days;b.classList.toggle('selected',on);b.setAttribute('aria-pressed',String(on));});
}
function stopAnimation() { clearInterval(animation);animation=null;$('play').textContent='▶ Iniciar animação'; }
function switchMode(mode) {
  if(mode===state.mode) return;
  stopAnimation();state.mode=mode;syncControls();render();
}
function showDetail(code) {
  const m=municipalities.get(code);if(!m)return;
  if(selectedCode!==code){selectedCode=code;state[state.mode].uf='';state[state.mode].search='';globalThis.PulsoMunicipio?.write(code);syncControls();render();return;}
  const total=lastTotals.get(code);
  const density=total==null?null:total/m.area_intersecao_km2*1000;
  $('detail').textContent=`${m.nome} · ${m.uf} — ${fmt(total)} focos registrados · ${fmt(density)} focos / 1.000 km². Área no recorte: ${fmt(m.area_intersecao_km2)} km².`;
}
function drawPointGroups() {
  if(pointLayer) {pointLayer.clearLayers();map.removeLayer(pointLayer);pointLayer=null;}
  if(!map || state.mode!=='recent' || state.recent.view!=='points' || !visiblePointRows.length)return;
  // Group only the viewport instead of constructing hundreds of thousands of DOM markers.
  const bounds=map.getBounds().pad(.08),zoom=map.getZoom(),groups=new Map();
  for(const r of visiblePointRows) {
    if(!bounds.contains([r[1],r[2]]))continue;
    const p=map.project([r[1],r[2]],zoom),key=Math.floor(p.x/48)+':'+Math.floor(p.y/48);
    let group=groups.get(key);
    if(!group){group={count:0,lat:0,lon:0,sample:r};groups.set(key,group);}
    group.count++;group.lat+=r[1];group.lon+=r[2];
  }
  pointLayer=L.layerGroup();
  for(const g of groups.values()) {
    const position=[g.lat/g.count,g.lon/g.count],r=g.sample;
    if(g.count===1)L.circleMarker(position,{radius:4,color:'#fff',weight:1,fillColor:'#cf552d',fillOpacity:.9})
      .bindPopup(`<strong>${esc(municipalities.get(r[4])?.nome||r[4])}</strong><br>${esc(r[3])}<br>${date(r[0])} (Brasília)`).addTo(pointLayer);
    else L.marker(position,{icon:L.divIcon({html:fmt(g.count),className:'cluster',iconSize:[42,42]}),title:`${g.count} focos próximos. Clique para aproximar.`})
      .bindPopup(`${fmt(g.count)} observações próximas. Aproxime para separar os registros.`)
      .on('click',()=>{if(map.getZoom()<18)map.setView(position,map.getZoom()+2);}).addTo(pointLayer);
  }
  pointLayer.addTo(map);
}
function paintMap(features, totals, metrics, rows, kind) {
  lastTotals=totals;lastFeatures=features;lastMetric=metrics;
  if(!map)return;
  if(mapLayer) map.removeLayer(mapLayer);
  if(pointLayer) {pointLayer.clearLayers();map.removeLayer(pointLayer);pointLayer=null;}
  lastTotals=totals;lastFeatures=features;lastMetric=metrics;
  const vals=[...metrics.values()].filter(Number.isFinite), max=state.mode==='history'?historyScale:Math.max(1,...vals.map(Math.abs));
  const diverging=['change','anomaly'].includes(kind);
  const palette=diverging?['#286e76','#a8cbd0','#eee9d9','#e6a575','#ae4b2b']:['#f9e9d0','#edbd89','#df8c53','#c55c30','#883f25'];
  function color(v) {
    if(v==null || !Number.isFinite(v))return '#dce1dc';
    if(v===0)return '#f1f4ef';
    return palette[diverging? Math.min(4,Math.max(0,Math.floor((v/max+1)*2.5))):Math.min(4,Math.floor(v/max*5))];
  }
  const points=state.mode==='recent' && state.recent.view==='points';
  mapLayer=L.geoJSON({type:'FeatureCollection',features},{style:f=>({color:'#6d8b7a',weight:.6,fillColor:points?'#dce8d9':color(metrics.get(f.properties.codigo_ibge)),fillOpacity:points?.12:.78}),onEachFeature:(f,l)=>{
    const p=f.properties, value=totals.get(p.codigo_ibge);
    l.bindTooltip(`${esc(p.nome)} · ${esc(p.uf)}<br>${fmt(value)} focos registrados`);
    l.on('click',()=>showDetail(p.codigo_ibge));
  }}).addTo(map);
  visiblePointRows=points?rows:[];
  const unit={total:'focos',density:'focos / 1.000 km²',change:'%',anomaly:'focos de diferença'}[kind];
  if(points) $('legend').innerHTML='<span><i class="swatch" style="background:#c55c30"></i>Foco observado</span><span>Círculos numerados agrupam registros próximos</span>';
  else {
    const labels=diverging?[`−${fmt(max)}`,`−${fmt(max*.5)}`,'0',fmt(max*.5),fmt(max)]:[0,1,2,3,4].map(i=>`${fmt(max*i/5)}–${fmt(max*(i+1)/5)}`);
    $('legend').innerHTML=`<strong>${esc(unit)}</strong>`+palette.map((c,i)=>`<span><i class="swatch" style="background:${c}"></i>${labels[i]}</span>`).join('')+'<span><i class="swatch" style="background:#f1f4ef"></i>Zero</span><span><i class="swatch" style="background:#dce1dc"></i>Sem dados</span>';
  }
  if(firstMap && features.length) {map.fitBounds(mapLayer.getBounds(),{padding:[8,8]});firstMap=false;}
  drawPointGroups();
}
function chart(series, title, subtitle) {
  $('chart-title').textContent=title;$('chart-subtitle').textContent=subtitle;
  if(!series.length){$('chart').innerHTML='<p class="empty">Nenhum dado disponível para este recorte.</p>';$('chart-table').innerHTML='';return;}
  const w=620,h=215,left=48,right=10,top=20,bottom=39;
  const max=Math.max(1,...series.map(x=>x.value||0)), width=(w-left-right)/series.length;
  let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}. Valores detalhados na tabela abaixo.">`;
  for(let i=0;i<=3;i++) {const y=top+(h-top-bottom)*i/3;svg+=`<line x1="${left}" x2="${w-right}" y1="${y}" y2="${y}" stroke="#e6ece5"/><text x="${left-7}" y="${y+4}" text-anchor="end">${fmt(max*(1-i/3))}</text>`;}
  series.forEach((v,i)=>{
    const x=left+i*width+width*.17,bh=(v.value||0)/max*(h-top-bottom),y=h-bottom-bh;
    svg+=v.value==null?`<text x="${x+width*.33}" y="${h-bottom-7}" text-anchor="middle">×</text>`:`<rect x="${x}" y="${y}" width="${width*.66}" height="${Math.max(1,bh)}" rx="2" fill="${v.partial?'#d5b889':'#38735a'}"><title>${esc(v.label)}: ${fmt(v.value)}${v.partial?' (parcial)':''}</title></rect>`;
    if(i%Math.ceil(series.length/8)===0 || i===series.length-1)svg+=`<text x="${x+width*.33}" y="${h-15}" text-anchor="middle">${esc(v.short||v.label)}</text>`;
  });
  $('chart').innerHTML=svg+'</svg>';
  $('chart-table').innerHTML='<table><thead><tr><th>Período</th><th>Focos</th><th>Cobertura</th></tr></thead><tbody>'+series.map(v=>`<tr><td>${esc(v.label)}</td><td>${v.value==null?'Sem dados':fmt(v.value)}</td><td>${v.value==null?'Ausente':v.partial?'Parcial':'Completa'}</td></tr>`).join('')+'</tbody></table>';
}
function ranking(totals) {
  const top=[...totals].filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).slice(0,10);
  $('ranking').innerHTML=top.length?top.map(([code,value])=>{const p=municipalities.get(code);return `<li><button class="rank-button" data-code="${esc(code)}"><span class="rank-name">${esc(p.nome)} <small>${esc(p.uf)}</small></span><strong>${fmt(value)}</strong></button></li>`;}).join(''):'<li class="empty">Nenhum foco registrado no recorte disponível.</li>';
  $('ranking').querySelectorAll('button').forEach(b=>b.onclick=()=>{showDetail(b.dataset.code);const f=lastFeatures.find(f=>f.properties.codigo_ibge===b.dataset.code);if(f && map)map.fitBounds(L.geoJSON(f).getBounds(),{maxZoom:10,padding:[24,24]});$('detail').scrollIntoView({behavior:globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});});
}
function summary(totals, features, partial=false) {
  $('total').textContent=fmt([...totals.values()].reduce((a,b)=>a+b,0));
  $('municipalities').textContent=fmt([...totals.values()].filter(x=>x>0).length);
  $('municipalities-note').textContent=`De ${fmt(features.length)} municípios no recorte`;
  $('total-note').textContent=partial?'Total observado · cobertura parcial':'No período e território selecionados';
  $('detail').textContent='Selecione um município no mapa ou no ranking.';
}
async function renderRecent(features,codes,token) {
  if(!recentMeta) recentMeta=await json('data/recentes.json');
  if(!recentMeta.dias)throw new Error('A base recente ainda não está disponível.');
  const now=Date.now(),start=now-state.recent.days*DAY;
  const covered=M.coverage(recentMeta,start,now);
  const parts=covered.filter(d=>d.arquivo);
  const records=(await Promise.all(parts.map(d=>blob(d.arquivo)))).flat();
  if(token!==sequence)return;
  const rows=M.recentRows(records,state.recent.days,now,codes), totals=M.totals(rows);
  const missing=covered.filter(d=>d.cobertura==='ausente').length;
  const incomplete=covered.some(d=>d.cobertura!=='completa');
  const stale=!recentMeta.ultima_consulta_ok || now-Date.parse(recentMeta.ultima_consulta_ok)>3600000;
  const anyCoverage=covered.some(d=>d.cobertura!=='ausente');
  for(const code of codes)if(!totals.has(code)&&anyCoverage)totals.set(code,0);
  summary(totals,features,incomplete);
  if(!anyCoverage){$('total').textContent='—';$('municipalities').textContent='—';}
  $('third-label').textContent='Observação mais recente';
  $('third').textContent=rows.length?date(rows.reduce((latest,r)=>r[0]>latest?r[0]:latest,rows[0][0])):'Sem registros';
  $('third-note').textContent='No recorte selecionado · horário de Brasília';
  $('period-label').textContent=`${date(start)} → ${date(now)} · horário de Brasília · janela móvel`;
  let message=`Última consulta bem-sucedida: ${date(recentMeta.ultima_consulta_ok)}. `;
  if(stale)message+='Atualização atrasada ou ainda não confirmada. ';
  if(!recentMeta.consulta_ok)message+='A última tentativa não confirmou atualização online. ';
  if(missing)message+=`${missing} dia(s) UTC sem arquivo disponível no período. `;
  if(incomplete)message+='Cobertura parcial: os totais refletem apenas os registros disponíveis. ';
  if(!features.length)message+='Nenhum município corresponde à busca.';
  notice(message,stale||incomplete||!recentMeta.consulta_ok?'warning':'');
  $('updated').textContent=`Base preparada: ${date(recentMeta.gerado_em)}`;
  $('map-subtitle').textContent='Aproxime os grupos para explorar as observações individuais.';
  paintMap(features,totals,totals,rows,'total');ranking(totals);
  const byDay=new Map();for(const r of rows){const key=M.localDay(r[0]);byDay.set(key,(byDay.get(key)||0)+1);}
  const localStart=M.localDay(start),localEnd=M.localDay(now),series=[];
  for(let t=Date.parse(localStart+'T12:00:00-03:00');M.localDay(t)<=localEnd;t+=DAY){
    const key=M.localDay(t),dayStart=Date.parse(key+'T00:00:00-03:00'),dayEnd=dayStart+DAY-1;
    const overlap=M.coverage(recentMeta,Math.max(start,dayStart),Math.min(now,dayEnd));
    const available=overlap.some(d=>d.cobertura!=='ausente');
    series.push({label:key.split('-').reverse().join('/'),short:key.slice(8)+'/'+key.slice(5,7),value:available?(byDay.get(key)||0):null,partial:overlap.some(d=>d.cobertura!=='completa')||dayStart<start||dayEnd>now});
  }
  chart(series,'Evolução diária','Horário de Brasília · barras claras: parcial · ×: sem dados.');
}
async function renderHistory(features,codes,token) {
  if(!historyMeta)historyMeta=await json('data/historico.json');
  if(!history)history=await blob(historyMeta.arquivo);
  if(token!==sequence)return;
  if(!state.history.year) {
    state.history.year=historyMeta.anos_completos.at(-1);
    $('year').innerHTML=historyMeta.anos_completos.map(y=>`<option>${y}</option>`).join('');
    $('year').value=state.history.year;
  }
  const {year,month,metric}=state.history;
  const totals=M.historyCounts(history,year,month,codes);
  const previous=M.historyCounts(history,year-1,month,codes);
  const base=historyMeta.anos_base.filter(y=>y!==year && historyMeta.anos_completos.includes(y));
  const means=new Map([...codes].map(code=>[code,0]));
  for(const y of base)for(const [code,value] of M.historyCounts(history,y,month,codes))means.set(code,means.get(code)+value/base.length);
  const values=new Map([...totals].map(([code,v])=>[code,metric==='density'?v/municipalities.get(code).area_intersecao_km2*1000:metric==='change'?M.change(v,previous.get(code)):metric==='anomaly'?(base.length?v-means.get(code):null):v]));
  summary(totals,features);
  $('third-label').textContent='Densidade no território';
  const total=[...totals.values()].reduce((a,b)=>a+b,0),area=features.reduce((n,f)=>n+f.properties.area_intersecao_km2,0);
  $('third').textContent=fmt(area?total/area*1000:null);$('third-note').textContent='Focos / 1.000 km² no recorte selecionado';
  $('period-label').textContent=`${month?months[month-1]+' de ':''}${year} · série de referência · ano completo validado`;
  notice(features.length?`Histórico independente dos registros operacionais. Base de comparação: ${base.length} anos completos disponíveis entre 2003 e 2025.`:'Nenhum município corresponde à busca.',features.length?'':'warning');
  $('updated').textContent=`Histórico preparado: ${date(historyMeta.gerado_em)}`;
  $('map-subtitle').textContent='Cada município é colorido pelo indicador selecionado.';
  const prev=previous.size?[...previous.values()].reduce((a,b)=>a+b,0):null;
  const mean=base.length?[...means.values()].reduce((a,b)=>a+b,0):null;
  const variation=M.change(total,prev),difference=mean==null?null:total-mean;
  $('comparison-text').textContent=`Variação em relação a ${year-1}: ${variation==null?'indisponível':fmt(variation)+'%'}. Diferença da média histórica para o mesmo período: ${difference==null?'indisponível':fmt(difference)+' focos'}.`;
  // One domain across all validated years for the current territory and period.
  historyScale=1;
  const allCounts=new Map(historyMeta.anos_completos.map(y=>[y,M.historyCounts(history,y,month,codes)]));
  for(const [y,counts] of allCounts)for(const [code,v] of counts){
    const ref=[...allCounts].filter(([other])=>other!==y && historyMeta.anos_base.includes(other)).map(([,c])=>c.get(code)).filter(Number.isFinite);
    const value=metric==='density'?v/municipalities.get(code).area_intersecao_km2*1000:metric==='change'?M.change(v,allCounts.get(y-1)?.get(code)):metric==='anomaly'?(ref.length?v-ref.reduce((a,b)=>a+b,0)/ref.length:null):v;
    if(Number.isFinite(value))historyScale=Math.max(historyScale,Math.abs(value));
  }
  paintMap(features,totals,values,[],metric);ranking(totals);
  const cells=M.calendar(history,historyMeta.anos_completos,codes);
  globalThis.PulsoCalendar?.(cells,year,month,(y,m)=>{stopAnimation();state.history.year=y;state.history.month=m;syncControls();render();});
  globalThis.PulsoComparison?.(M.comparison(cells,year,historyMeta.anos_completos),year);
  let series;
  if(!month) {
    series=months.map((label,i)=>({label,short:label.slice(0,3),value:cells.find(c=>c.year===year&&c.month===i+1)?.value??null}));
    chart(series,`Evolução mensal · ${year}`,'Distribuição dos focos ao longo do ano selecionado.');
  } else {
    series=historyMeta.anos_completos.map(y=>({label:String(y),value:cells.find(c=>c.year===y&&c.month===month)?.value??null}));
    chart(series,`${months[month-1]} ao longo dos anos`,'Comparação do mesmo mês na série de referência.');
  }
}
async function render() {
  if(!geo)return;
  const token=++sequence,features=subset(),codes=new Set(features.map(f=>f.properties.codigo_ibge));
  $('main').setAttribute('aria-busy','true');notice('Carregando o recorte selecionado…');
  try {
    if(state.mode==='recent')await renderRecent(features,codes,token);else await renderHistory(features,codes,token);
    if(token===sequence){globalThis.PulsoMunicipio?.render(municipalities.get(selectedCode),lastTotals.get(selectedCode));if(selectedCode)showDetail(selectedCode);}
  } catch(error) {
    if(token!==sequence)return;
    notice('Não foi possível carregar este recorte. '+error.message+' Tente novamente pelo botão Limpar filtros.','error');
    ['total','municipalities','third'].forEach(id=>$(id).textContent='—');
    if(mapLayer)map.removeLayer(mapLayer);if(pointLayer){pointLayer.clearLayers();map.removeLayer(pointLayer);}
    visiblePointRows=[];
    $('ranking').innerHTML='';$('chart').innerHTML='<p class="empty">Dados indisponíveis.</p>';$('chart-table').innerHTML='';$('legend').innerHTML='';$('detail').textContent='Dados indisponíveis para este recorte.';$('comparison-text').textContent='Comparação indisponível.';
  } finally {if(token===sequence)$('main').removeAttribute('aria-busy');}
}
async function refresh() {
  if(document.hidden)return;
  try {
    const next=await json('data/recentes.json');
    // Fetch the selected partitions before swapping manifests so failures retain the visible data.
    if(state.mode==='recent') {
      const now=Date.now();await Promise.all(M.coverage(next,now-state.recent.days*DAY,now).filter(d=>d.arquivo).map(d=>blob(d.arquivo)));
    }
    recentMeta=next;
    const keep=new Set([historyMeta?.arquivo,...(next.dias||[]).map(d=>d.arquivo)]);
    for(const key of cache.keys())if(!keep.has(key))cache.delete(key);
    if(state.mode==='recent')await render();
  } catch(error) {if(state.mode==='recent')notice('Falha ao consultar a atualização. Os últimos dados carregados foram preservados. Última consulta confirmada: '+date(recentMeta?.ultima_consulta_ok)+'.','warning');}
}
function ensureMap() {
  if(map)return;
  $('map').hidden=false;$('load-map').hidden=true;
    map=L.map('map',{preferCanvas:true}).setView([-5.5,-58],5);
    map.on('moveend',drawPointGroups);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:18}).addTo(map);
}
async function init() {
  try {
    if(typeof L==='undefined' || typeof pako==='undefined')throw new Error('Não foi possível carregar os recursos do mapa. Verifique sua conexão.');
    $('load-map').onclick=()=>{ensureMap();render();};
    if(!globalThis.matchMedia?.('(max-width: 850px)').matches)ensureMap();else {$('map').hidden=true;$('load-map').hidden=false;}
    geo=await json('data/municipios_amazonia_legal_web.geojson');
    municipalities=new Map(geo.features.map(f=>[String(f.properties.codigo_ibge),f.properties]));
    selectedCode=globalThis.PulsoMunicipio?.read(new Set(municipalities.keys()))||null;
    $('municipal-options').innerHTML=[...municipalities.values()].map(m=>`<option value="${esc(m.nome)} · ${esc(m.uf)}"></option>`).join('');
    $('municipal-clear').onclick=()=>{selectedCode=null;globalThis.PulsoMunicipio?.write(null);render();};
    globalThis.PulsoNarrative?.();
    $('state').innerHTML+=[...new Set(geo.features.map(f=>f.properties.uf))].sort().map(uf=>`<option>${esc(uf)}</option>`).join('');
    $('month').innerHTML+=months.map((m,i)=>`<option value="${i+1}">${m}</option>`).join('');
    $('nav-recent').onclick=()=>switchMode('recent');$('nav-history').onclick=()=>switchMode('history');
    document.querySelector('.brand').onclick=()=>switchMode('recent');
    document.querySelectorAll('[data-days]').forEach(b=>b.onclick=()=>{state.recent.days=Number(b.dataset.days);syncControls();render();});
    $('state').onchange=()=>{selectedCode=null;globalThis.PulsoMunicipio?.write(null);state[state.mode].uf=$('state').value;render();};
    let searchTimer;$('search').oninput=()=>{const value=$('search').value;const exact=[...municipalities.values()].find(m=>m.nome+' · '+m.uf===value);selectedCode=exact?mCode(exact):null;globalThis.PulsoMunicipio?.write(selectedCode);state[state.mode].search=exact?'':value;clearTimeout(searchTimer);searchTimer=setTimeout(render,180);};
    $('year').onchange=()=>{stopAnimation();state.history.year=Number($('year').value);render();};
    $('month').onchange=()=>{state.history.month=Number($('month').value);render();};
    $('metric').onchange=()=>{state.history.metric=$('metric').value;render();};
    $('view').onchange=()=>{state.recent.view=$('view').value;render();};
    $('clear').onclick=()=>{selectedCode=null;globalThis.PulsoMunicipio?.write(null);stopAnimation();if(state.mode==='recent'){state.recent={days:7,uf:'',search:'',view:'points'};recentMeta=null;}else state.history={year:historyMeta?.anos_completos.at(-1)||null,month:0,uf:'',search:'',metric:'total'};syncControls();render();};
    $('play').onclick=()=>{if(animation){stopAnimation();return;}if(!historyMeta)return;if(globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches){notice('Movimento reduzido ativado. Use o seletor de ano para avançar manualmente.');return;}$('play').textContent='Ⅱ Pausar animação';animation=setInterval(()=>{const ys=historyMeta.anos_completos;state.history.year=ys[(ys.indexOf(state.history.year)+1)%ys.length];$('year').value=state.history.year;render();},1800);};
    document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAnimation();else refresh();});
    syncControls();await render();setInterval(refresh,300000);
  } catch(error) {notice(error.message,'error');}
}
init();
