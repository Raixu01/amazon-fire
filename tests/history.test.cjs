const {test}=require('node:test');
const assert=require('node:assert/strict');
const M=require('../docs/model.js');
test('calendar distinguishes explicit zero from absent and incomplete municipal coverage',()=>{
  const data={mensais:[['A',2024,1,0],['B',2024,1,0],['A',2024,2,5]]};
  const cells=M.calendar(data,[2024],new Set(['A','B']));
  assert.equal(cells[0].value,0);assert.equal(cells[1].value,null);assert.equal(cells[2].value,null);
  assert.equal(M.calendar(data,[2024],new Set())[0].value,null);
});
test('historical band excludes selected year and incomplete years, with interpolated quartiles',()=>{
  const cells=[2020,2021,2022,2023,2024].flatMap((year,i)=>Array.from({length:12},(_,m)=>({year,month:m+1,value:i===4?10000:i*10})));
  cells.find(c=>c.year===2023&&c.month===12).value=null;
  const rows=M.comparison(cells,2024,[2020,2021,2022,2023,2024]);
  assert.deepEqual(rows[0],{month:1,value:10000,low:5,median:10,high:15,n:3});
  assert.equal(rows[11].n,3);
  assert.equal(M.comparison(cells,2024,[2024])[0].median,null);
});
test('municipal selection validates codes and preserves leading digits',()=>{
  const codes=new Set(['1506807','0100001']);
  assert.equal(M.municipalCode('1506807',codes),'1506807');
  assert.equal(M.municipalCode('0100001',codes),'0100001');
  assert.equal(M.municipalCode('unknown',codes),null);
});
test('shared municipal URL preserves unrelated parameters and can be cleared',()=>{
  const vm=require('node:vm'),fs=require('node:fs');let url='http://localhost:8765/?other=1&municipio=1506807';
  const context=vm.createContext({FireModel:M,URL,location:{href:url},history:{replaceState(a,b,next){url=String(next);context.location.href=url;}}});
  vm.runInContext(fs.readFileSync('docs/components/municipio.js','utf8'),context);
  assert.equal(context.PulsoMunicipio.read(new Set(['1506807'])),'1506807');
  context.PulsoMunicipio.write('0100001');assert.match(url,/municipio=0100001/);
  context.PulsoMunicipio.write(null);assert.equal(url,'http://localhost:8765/?other=1');
});
