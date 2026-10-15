const {test} = require('node:test');
const assert = require('node:assert/strict');
const M = require('../docs/model.js');
test('rolling window crosses months and excludes future and foreign municipality',()=>{
  const now=Date.parse('2026-01-01T12:00:00Z'), codes=new Set(['A']);
  const row=(time,code='A')=>[time,0,0,'GOES',code];
  const rows=[row('2025-12-31T12:00:00Z'),row('2025-12-31T11:59:59Z'),row('2026-01-02T00:00:00Z'),row('2026-01-01T01:00:00Z','B')];
  assert.equal(M.recentRows(rows,1,now,codes).length,1);
});
test('monthly filtering uses monthly rows and never annual totals',()=>{
  const data={anuais:[['A',2025,30]],mensais:[['A',2025,1,10],['A',2025,2,20]]};
  assert.equal(M.historyCounts(data,2025,1,new Set(['A'])).get('A'),10);
  assert.equal(M.historyCounts(data,2025,0,new Set(['A'])).get('A'),30);
});
test('unavailable previous year is not a zero percent change',()=>{
  assert.equal(M.change(20,undefined),null);assert.equal(M.change(20,0),null);assert.equal(M.change(20,10),100);
});
test('coverage exposes absent dates across a year boundary',()=>{
  const c=M.coverage({dias:[{dia:'2025-12-31',cobertura:'completa'}]},Date.parse('2025-12-31T12:00Z'),Date.parse('2026-01-01T12:00Z'));
  assert.deepEqual(c.map(x=>x.cobertura),['completa','ausente']);
});
test('Brasilia date differs from UTC around midnight',()=>assert.equal(M.localDay('2026-10-15T01:00:00Z'),'2026-10-14'));
test('all displayed municipal counts add up to observations',()=>{
  const rows=[['x',0,0,'G','A'],['x',0,0,'G','A'],['x',0,0,'G','B']];
  assert.equal([...M.totals(rows).values()].reduce((a,b)=>a+b,0),rows.length);
});
