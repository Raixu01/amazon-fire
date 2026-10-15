/* Pure data operations shared by the interface and regression tests. */
(function(root) {
  const dayMs = 86400000;
  const localDay = stamp => new Intl.DateTimeFormat('en-CA', {timeZone:'America/Sao_Paulo', year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(stamp));
  function recentRows(records, days, now, codes) {
    const start = now - days * dayMs;
    return records.filter(r => Date.parse(r[0]) >= start && Date.parse(r[0]) <= now && codes.has(r[4]));
  }
  function totals(records) {
    const result = new Map();
    for (const r of records) result.set(r[4], (result.get(r[4]) || 0) + 1);
    return result;
  }
  function historyCounts(data, year, month, codes) {
    return new Map((month ? data.mensais : data.anuais)
      .filter(r => r[1] === year && (!month || r[2] === month) && codes.has(r[0]))
      .map(r => [r[0], r[month ? 3 : 2]]));
  }
  function change(value, previous) {
    return previous == null || previous === 0 ? null : (value - previous) / previous * 100;
  }
  function coverage(manifest, start, end) {
    const days = new Map((manifest.dias || []).map(d => [d.dia, d]));
    const result = [];
    for(let time = Math.floor(start/dayMs)*dayMs; time <= end; time += dayMs) {
      const key = new Date(time).toISOString().slice(0,10);
      result.push(days.get(key) || {dia:key,cobertura:'ausente'});
    }
    return result;
  }
  function calendar(data, years, codes) {
    const sums = new Map(), counts = new Map();
    for(const [code,year,month,value] of data.mensais) {
      if(!codes.has(code) || !Number.isFinite(value))continue;
      const key=year+':'+month;
      sums.set(key,(sums.get(key)||0)+value);
      if(!counts.has(key))counts.set(key,new Set());
      counts.get(key).add(code);
    }
    return years.flatMap(year=>Array.from({length:12},(_,i)=>{
      const month=i+1,key=year+':'+month;
      return {year,month,value:codes.size && counts.get(key)?.size===codes.size?sums.get(key):null};
    }));
  }
  function quantile(values,p) {
    const sorted=values.filter(Number.isFinite).sort((a,b)=>a-b);
    if(!sorted.length)return null;
    const index=(sorted.length-1)*p,lo=Math.floor(index);
    return sorted[lo]+(sorted[Math.ceil(index)]-sorted[lo])*(index-lo);
  }
  function comparison(cells,year,validYears) {
    const reference=validYears.filter(y=>y!==year && cells.filter(c=>c.year===y && c.value!==null).length===12);
    return Array.from({length:12},(_,i)=>{
      const month=i+1,values=cells.filter(c=>c.month===month && reference.includes(c.year)).map(c=>c.value);
      return {month,value:cells.find(c=>c.year===year && c.month===month)?.value??null,
        low:quantile(values,.25),median:quantile(values,.5),high:quantile(values,.75),n:values.length};
    });
  }
  function municipalCode(value,codes) { return codes.has(value)?value:null; }
  const api = {dayMs,localDay,recentRows,totals,historyCounts,change,coverage,calendar,quantile,comparison,municipalCode};
  if (typeof module !== 'undefined') module.exports = api;
  root.FireModel = api;
})(globalThis);
