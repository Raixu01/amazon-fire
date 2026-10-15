/* UI state integration in a simulated DOM; this is not a visual browser test. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const zlib = require('node:zlib');
class Element {
  constructor(){this.textContent='';this.innerHTML='';this.hidden=false;this.value='';this.dataset={};this.attributes={};this.classList={toggle(){}};}
  setAttribute(k,v){this.attributes[k]=v;}
  removeAttribute(k){delete this.attributes[k];}
  querySelectorAll(){return [];}
  scrollIntoView(){}
}
function layer(){return {addTo(){return this;},on(){return this;},bindPopup(){return this;},bindTooltip(){return this;},clearLayers(){},getBounds(){return {};}};}
test('screen switching, independent filters, monthly data, missing comparisons and refresh failure',async()=>{
  const html=fs.readFileSync('docs/index.html','utf8');
  const elements=new Map([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
  const periods=[1,3,7,30].map(n=>Object.assign(new Element(),{dataset:{days:String(n)}}));
  const document={body:new Element(),hidden:false,getElementById:id=>{assert.ok(elements.has(id),'unknown element '+id);return elements.get(id);},querySelector:()=>new Element(),querySelectorAll:()=>periods,addEventListener(){}};
  const geo={type:'FeatureCollection',features:['A','B'].map((code,i)=>({type:'Feature',geometry:{type:'Point',coordinates:[-54,-2]},properties:{codigo_ibge:code,nome:i?'Belém':'Santarém',uf:'PA',area_intersecao_km2:100}}))};
  const history={anuais:[['A',2024,10],['B',2024,20],['A',2025,30],['B',2025,10]],mensais:[['A',2025,1,5],['B',2025,1,2]]};
  const manifest={gerado_em:'2026-01-01T12:00Z',ultima_consulta_ok:'2026-01-01T12:00Z',consulta_ok:true,dias:[{dia:'2025-12-31',arquivo:'d1.gz',cobertura:'completa'},{dia:'2026-01-01',arquivo:'d2.gz',cobertura:'parcial'}]};
  const datasets={
    'data/municipios_amazonia_legal_web.geojson':geo,
    'data/recentes.json':manifest,
    'data/historico.json':{anos_completos:[2024,2025],anos_base:[2024,2025],arquivo:'h.gz',gerado_em:'2026-01-01T12:00Z'},
    'data/h.gz':history,
    'data/d1.gz':[['2025-12-31T18:00Z',-2,-54,'GOES','A']],
    'data/d2.gz':[['2026-01-01T09:00Z',-2,-54,'GOES','A'],['2026-01-01T10:00Z',-2,-54,'GOES','B']],
  };
  let offline=false,fitCount=0;
  const fetch=async url=>{if(offline)throw new Error('offline');assert.ok(url in datasets,url);return {ok:true,json:async()=>datasets[url],arrayBuffer:async()=>new TextEncoder().encode(JSON.stringify(datasets[url])).buffer};};
  class Clock extends Date {static now(){return Date.parse('2026-01-01T12:00Z');}}
  const map={...layer(),setView(){return this;},fitBounds(){fitCount++;},removeLayer(){},getBounds(){return {pad(){return this;},contains(){return true;}};},getZoom(){return 5;},project(){return {x:1,y:1};}};
  const L={map:()=>map,tileLayer:layer,geoJSON:layer,layerGroup:layer,circleMarker:layer,marker:layer,divIcon:x=>x};
  const context=vm.createContext({document,L,fetch,Intl,Date:Clock,TextDecoder,Uint8Array,console,setTimeout,clearTimeout,setInterval:()=>1,clearInterval(){},pako:{ungzip:zlib.gunzipSync}});
  vm.runInContext(fs.readFileSync('docs/model.js','utf8'),context);
  vm.runInContext(fs.readFileSync('docs/app.js','utf8').replace(/init\(\);\s*$/,'globalThis.ready=init();'),context);
  await context.ready;
  assert.equal(elements.get('total').textContent,'3');
  assert.equal(elements.get('title').textContent,'Monitoramento recente');
  await vm.runInContext("state.recent.days=3;state.recent.search='santarem';render()",context);
  assert.equal(elements.get('total').textContent,'2');
  await vm.runInContext("state.mode='history';syncControls();render()",context);
  assert.equal(elements.get('title').textContent,'Análise histórica');
  assert.equal(elements.get('total').textContent,'40');
  await vm.runInContext("state.history.month=1;render()",context);
  assert.equal(elements.get('total').textContent,'7');
  assert.match(elements.get('comparison-text').textContent,/indisponível/);
  await vm.runInContext("state.mode='recent';syncControls();render()",context);
  assert.equal(elements.get('search').value,'santarem');
  assert.equal(elements.get('total').textContent,'2');
  assert.equal(vm.runInContext('state.history.month',context),1);
  assert.equal(vm.runInContext('state.recent.days',context),3);
  const fits=fitCount;await vm.runInContext('refresh()',context);assert.equal(fitCount,fits);
  offline=true;await vm.runInContext('refresh()',context);
  assert.equal(elements.get('total').textContent,'2');
  assert.match(elements.get('status').textContent,/preservados/);
  offline=false;
  await vm.runInContext("state.recent.search='inexistente';render()",context);
  assert.match(elements.get('status').textContent,/Nenhum município/);
  await vm.runInContext("state.recent.search='';selectedCode='A';render()",context);
  assert.equal(elements.get('total').textContent,'2');
  assert.match(elements.get('detail').textContent,/Santarém/);
  await vm.runInContext("state.mode='history';syncControls();render()",context);
  assert.equal(elements.get('total').textContent,'5');
  await vm.runInContext("selectedCode=null;render()",context);
  assert.equal(elements.get('total').textContent,'7');
});
