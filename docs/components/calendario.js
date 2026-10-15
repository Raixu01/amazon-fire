globalThis.PulsoCalendar = function(cells,year,month,onSelect) {
  const host=document.getElementById('calendar-plot');
  const max=Math.max(1,...cells.map(d=>d.value||0));
  const names=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
  if(globalThis.Plot)host.replaceChildren(Plot.plot({width:Math.max(300,host.clientWidth),height:cells.length/12*23+65,marginLeft:48,
    x:{domain:names,label:null,axis:'top'},y:{domain:[...new Set(cells.map(d=>d.year))].reverse(),label:null},
    color:{domain:[0,max],scheme:'YlOrRd',legend:true,label:'Focos · escala comum a todos os anos'},
    marks:[Plot.cell(cells,{x:d=>names[d.month-1],y:'year',fill:'#e0e5e1'}),
      Plot.cell(cells.filter(d=>d.value!==null),{x:d=>names[d.month-1],y:'year',fill:'value',inset:1,title:d=>`${d.year} · ${names[d.month-1]}: ${d.value.toLocaleString('pt-BR')} focos`}),
      Plot.cell(cells.filter(d=>d.year===year&&(!month||d.month===month)),{x:d=>names[d.month-1],y:'year',fill:null,stroke:'#173d32',strokeWidth:2,inset:1})]}));
  document.getElementById('calendar-summary').textContent=`${cells.length/12} anos. Células cinza indicam dados ausentes; zero tem a cor mínima da escala. Selecione um período na tabela ou nos filtros.`;
  const table=document.getElementById('calendar-table');
  table.innerHTML='<table><caption>Calendário mensal — selecione um mês</caption><thead><tr><th>Ano</th>'+names.map(n=>`<th>${n}</th>`).join('')+'</tr></thead><tbody>'+[...new Set(cells.map(d=>d.year))].reverse().map(y=>'<tr><th>'+y+'</th>'+cells.filter(d=>d.year===y).map(d=>`<td><button data-year="${y}" data-month="${d.month}" aria-label="${names[d.month-1]} de ${y}: ${d.value??'sem dados'} focos">${d.value===null?'—':d.value.toLocaleString('pt-BR')}</button></td>`).join('')+'</tr>').join('')+'</tbody></table>';
  table.querySelectorAll('button').forEach(b=>b.onclick=()=>onSelect(Number(b.dataset.year),Number(b.dataset.month)));
};
