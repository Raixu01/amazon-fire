globalThis.PulsoComparison = function(rows,year) {
  const host=document.getElementById('historical-plot'),names=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
  if(globalThis.Plot)host.replaceChildren(Plot.plot({width:Math.max(300,host.clientWidth),height:300,marginLeft:65,
    x:{domain:[1,12],ticks:12,tickFormat:m=>names[m-1],label:null},y:{grid:true,zero:true,label:'Focos'},
    marks:[Plot.areaY(rows,{x:'month',y1:'low',y2:'high',fill:'#b8d4c4'}),Plot.lineY(rows,{x:'month',y:'median',stroke:'#28654e',strokeDasharray:'5,4'}),Plot.lineY(rows,{x:'month',y:'value',stroke:'#c6572e',strokeWidth:2.5}),Plot.dot(rows,{x:'month',y:'value',fill:'#c6572e',title:d=>`${names[d.month-1]}: ${d.value??'sem dados'}`})]}));
  const f=v=>v===null?'Sem dados':v.toLocaleString('pt-BR',{maximumFractionDigits:1});
  document.getElementById('historical-summary').textContent=`Linha laranja: ${year}. Linha verde tracejada: mediana. Faixa verde: percentis 25 a 75 (metade central dos valores), não uma previsão. Referência: ${rows[0].n} anos completos válidos, excluindo ${year}. Meses equivalentes da série de referência.`;
  document.getElementById('historical-table').innerHTML='<table><caption>Comparação mensal com a referência</caption><thead><tr><th>Mês</th><th>'+year+'</th><th>P25</th><th>Mediana</th><th>P75</th></tr></thead><tbody>'+rows.map(r=>`<tr><th>${names[r.month-1]}</th><td>${f(r.value)}</td><td>${f(r.low)}</td><td>${f(r.median)}</td><td>${f(r.high)}</td></tr>`).join('')+'</tbody></table>';
};
