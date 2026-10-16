import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, Easing} from 'remotion';
import D from './atm-dados.json';

const C={bg:'#091b24',panel:'#112a35',white:'#f3f6f3',muted:'#b7c9cb',orange:'#ff774c',cyan:'#65dbce',gold:'#ffe49a'};
const months=['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT'];
const monthNames=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro'];
const days=Object.keys(D.daily), monthKeys=Object.keys(D.monthly);
const n=x=>new Intl.NumberFormat('pt-BR').format(x);
const clamp=(f,a,b)=>interpolate(f,[a,b],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
const T=({children,size=27,color=C.white,style={}})=><div style={{fontSize:size,lineHeight:1.22,color,...style}}>{children}</div>;
const Tag=({children})=><T size={21} color={C.cyan} style={{fontWeight:700,letterSpacing:2,marginBottom:24}}>{children}</T>;
function Brand({large=false,frame=150}){
  const w=large?600:216;
  return <div style={{display:'flex',alignItems:'center',gap:large?40:22,color:'#091b24'}}>
    <div style={{width:w,height:w*322/1184,position:'relative',overflow:'hidden',opacity:clamp(frame,0,25)}}>
      <Img src={staticFile('atm/pulso-original.jpeg')} style={{position:'absolute',width:w*1920/1184,maxWidth:'none',left:-w*367/1184,top:-w*427/1184}} />
    </div>
    <div style={{height:large?146:56,width:large?3:2,background:'#18333e',transform:`scaleY(${clamp(frame,25,48)})`}} />
    <div style={{fontSize:large?146:54,fontWeight:600,letterSpacing:-3,opacity:clamp(frame,48,73)}}><span style={{color:'#0c897c'}}>.</span>atm</div>
  </div>;
}
function Header({title,sub}){return <div style={{position:'absolute',inset:'0 0 auto',height:140,background:'#fff',display:'flex',alignItems:'center',padding:'0 46px',gap:65}}>
  <Brand/><div style={{height:62,width:1,background:'#cbd6d7'}}/><div><T size={34} color='#091b24' style={{fontWeight:700}}>{title}</T>{sub&&<T size={21} color='#48626b' style={{marginTop:8}}>{sub}</T>}</div>
</div>;}
function Map({zoom=0,layer=null,region=false,labels=false,allMunicipios=false}){
  const box=D.nationalBox.map((v,i)=>v+(D.regionalBox[i]-v)*zoom);
  const img=(src,b,opacity=1)=><image href={staticFile(`atm/${src}`)} x={b[0]} y={b[1]} width={b[2]} height={b[3]} opacity={opacity}/>;
  return <div style={{position:'absolute',left:600,top:192,width:1280,height:810,borderRadius:16,overflow:'hidden',background:'#16343c',border:'1px solid #37505a'}}>
    <svg width='1280' height='810' viewBox={box.join(' ')}>
      {img('amazonia.jpg',D.nationalBox)}
      {zoom>.5&&img('regiao.jpg',D.regionalBox,clamp(zoom,.5,1))}
      <rect x={box[0]} y={box[1]} width={box[2]} height={box[3]} fill='#001521' opacity='.33'/>
      <path d={D.legalPath} fill='none' stroke={C.cyan} strokeWidth={2} vectorEffect='non-scaling-stroke' opacity={1-zoom*.75}/>
      {allMunicipios&&D.allPaths.map((p,i)=><path key={`municipio-${i}`} d={p} fill='none' stroke='#b7d2d0' strokeWidth={.55} vectorEffect='non-scaling-stroke' opacity={1-zoom}/>) }
      {D.paths.map(p=><path key={p.code} d={p.path} fill={p.code==='1500602'?'#ffe49a':'none'} fillOpacity='.035' stroke={p.code==='1500602'?C.gold:p.chosen?'#c2d2cf':'#7a989d'} strokeWidth={p.code==='1500602'?2.8:p.chosen?1.4:.7} vectorEffect='non-scaling-stroke' opacity={zoom}/>) }
      {layer&&img(layer,region?D.regionalBox:D.nationalBox)}
    </svg>
    {labels&&D.labels.map(p=>{
      const x=(p.x-box[0])/box[2]*1280,y=(p.y-box[1])/box[3]*810;
      const offsets={'1508159':[-4,-38],'1505650':[-50,-14],'1500602':[25,5]};const o=offsets[p.code]||[0,0];
      return <div key={p.code} style={{position:'absolute',left:x+o[0],top:y+o[1],transform:'translate(-50%,-50%)',whiteSpace:'nowrap',padding:'5px 9px',borderRadius:5,background:'rgba(4,24,32,.82)',fontSize:21,color:p.code==='1500602'?C.gold:C.white,fontWeight:600}}>{p.name}</div>;
    })}
    <div style={{position:'absolute',right:20,top:18,fontSize:22,fontWeight:700}}>N ↑</div>
    <div style={{position:'absolute',left:18,bottom:14,fontSize:19,color:'#e0ebdf',padding:'5px 10px',background:'rgba(4,24,32,.8)'}}>Imagem de referência • mosaico de datas diversas</div>
  </div>;
}
const Side=({children})=><div style={{position:'absolute',left:46,top:190,width:510,height:814}}>{children}</div>;
const SourceNote=()=> <div style={{position:'absolute',bottom:35,left:0,right:0}}><T size={21} color={C.muted}>Cada ponto é uma detecção.<br/>Não representa um incêndio único.</T><T size={19} color={C.cyan} style={{marginTop:18}}>Fonte: INPE — Focos de Queimadas e Incêndios, CSV Brasil</T></div>;
function Legend({national=false}){return <div style={{padding:'23px 25px',border:'1px solid #37505a',borderRadius:14,marginTop:30,background:C.panel}}>
  <T size={22} color={C.cyan} style={{fontWeight:700,letterSpacing:1}}>COMO LER O MAPA</T>
  <T size={24} style={{marginTop:20}}><span style={{color:C.orange}}>●</span> Focos do período exibido</T>
  <T size={24} style={{marginTop:14}}><span style={{color:national?C.cyan:C.gold}}>━</span> {national?'Amazônia Legal':'Limite de Altamira'}</T>
  {!national&&<T size={24} style={{marginTop:14}}>━ Municípios vizinhos</T>}
  <T size={22} color={C.muted} style={{marginTop:20}}>Cada ponto é uma detecção.<br/>Não representa um incêndio único.</T>
</div>;}
function MonthlyChart({index}){const max=Math.max(...Object.values(D.monthly));return <div style={{marginTop:32}}>{monthKeys.map((k,j)=><div key={k} style={{display:'flex',alignItems:'center',height:35,gap:12,opacity:j<=index?1:.38}}>
  <T size={20} color={j===index?C.white:C.muted} style={{width:49}}>{months[j]}{j===9?'*':''}</T>
  <div style={{width:270,height:12,background:'#1d3a45',borderRadius:3}}><div style={{height:'100%',width:`${D.monthly[k]/max*100}%`,background:j===index?C.orange:C.cyan,borderRadius:3}}/></div>
  <T size={20} style={{width:100,textAlign:'right'}}>{j<=index?n(D.monthly[k]):'—'}</T>
</div>)}<T size={19} color={C.muted} style={{marginTop:12}}>* Outubro: 1–15, período parcial.</T></div>;}
function DailyChart({index}){const max=Math.max(...Object.values(D.daily));return <div style={{marginTop:28}}>
  <div style={{height:120,display:'flex',alignItems:'flex-end',gap:9}}>{days.map((d,i)=><div key={d} style={{flex:1,height:`${Math.max(3,D.daily[d]/max*100)}%`,background:i===index?C.orange:i<index?C.cyan:'#29434d',borderRadius:'4px 4px 0 0'}}/>)}</div>
  <div style={{display:'flex',gap:9,marginTop:8}}>{days.map((d,i)=><div key={d} style={{flex:1,textAlign:'center',fontSize:16,color:i===index?C.orange:C.muted}}>{i+1}</div>)}</div>
  <T size={20} color={C.muted} style={{marginTop:15}}>Detecções por dia • 15/10 parcial</T>
</div>;}
function Opening({frame}){return <AbsoluteFill style={{background:'#fff',color:C.bg,alignItems:'center',justifyContent:'center',fontFamily:'Arial, Helvetica, sans-serif'}}>
  <div style={{transform:`translateY(${interpolate(frame,[0,30],[18,0],{extrapolateRight:'clamp'})}px)`}}><Brand large frame={frame}/></div>
  <div style={{opacity:clamp(frame,78,105),marginTop:68,textAlign:'center'}}><T size={31} color='#34545c' style={{letterSpacing:5}}>AMAZÔNIA EM OBSERVAÇÃO</T><T size={24} color='#56717a' style={{marginTop:20}}>2026 • Da Amazônia Legal à região de Altamira</T></div>
  <div style={{position:'absolute',bottom:0,left:0,height:7,background:'#0c897c',width:`${clamp(frame,0,149)*100}%`}}/>
</AbsoluteFill>;}
function Credits(){return <><Header title='Fontes, método e créditos' sub='Pulso | .ATM • edição de 15 de outubro de 2026'/><div style={{position:'absolute',left:70,top:195,right:70}}>
  <Tag>FONTES DOS DADOS</Tag><T size={38} style={{fontWeight:700}}>INPE / Programa Queimadas</T>
  <T size={28} style={{marginTop:16}}>Base: Focos de Queimadas e Incêndios • CSV Brasil</T>
  <div style={{marginTop:26,padding:25,background:C.panel,borderRadius:14}}><T size={25}>Mensais: focos_mensal_br_202601.csv … focos_mensal_br_202609.csv</T><T size={25} style={{marginTop:13}}>Diários: focos_diario_br_20261001.csv … focos_diario_br_20261015.csv</T></div>
  <T size={25} color={C.cyan} style={{marginTop:28}}>Filtro: NOAA-20 • horários em Brasília • corte: {D.cutoff}</T>
  <T size={24} color={C.muted} style={{marginTop:18}}>Dia 15 e mês de outubro parciais. Focos não equivalem a incêndios únicos ou área queimada.</T>
  <T size={24} style={{marginTop:30}}>Limites: IBGE — Amazônia Legal e municípios, 2024.</T>
  <T size={23} color={C.muted} style={{marginTop:16}}>Imagem: Esri, Vantor, Earthstar Geographics e GIS User Community — mosaico de datas diversas.</T>
  <T size={24} style={{marginTop:32}}>Auditoria, tabelas e camadas: github.com/Raixu01/amazon-fire</T>
  <T size={22} color={C.muted} style={{marginTop:15}}>Fonte: data.inpe.br/queimadas/dados-abertos/ • Produção: Pulso | .ATM • Remotion</T>
</div></>;}
export function ATMVideo({preview=false}){
  const raw=useCurrentFrame();const f=preview&&raw>=150?raw-150+1020:raw;
  if(f<150)return <Opening frame={f}/>;
  let content;
  if(f<360){content=<><Header title='O ano na Amazônia Legal' sub='01/01 a 15/10/2026 • Amazônia Legal brasileira'/><Map/><Side><Tag>01 / VISÃO GERAL</Tag><T size={53} style={{fontWeight:700}}>Um território.<br/>Dez meses de<br/>observação.</T><T size={27} color={C.muted} style={{marginTop:30}}>Acompanhe os focos detectados por satélite e a mudança de escala até Altamira.</T><Legend national/><T size={21} color={C.muted} style={{marginTop:22}}>Mesmo sensor em toda a análise: NOAA-20.</T></Side></>;}
  else if(f<1020){const i=Math.min(8,Math.floor((f-360)/660*9));content=<><Header title='Evolução mensal dos focos' sub='Janeiro a setembro de 2026 • NOAA-20 • horários em Brasília'/><Map layer={`mes-${monthKeys[i]}.png`}/><Side><Tag>02 / AMAZÔNIA LEGAL</Tag><T size={48} style={{fontWeight:700}}>{monthNames[i]} <span style={{color:C.muted}}>2026</span></T><T size={76} color={C.orange} style={{fontWeight:700,marginTop:20}}>{n(D.monthly[monthKeys[i]])}</T><T size={26}>detecções no mês</T><MonthlyChart index={i}/><T size={24} color={C.muted} style={{marginTop:27}}>● Os pontos mudam a cada mês.<br/>Exibição sem acúmulo temporal.</T></Side></>;}
  else if(f<1260){const z=interpolate(f,[1080,1248],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)});content=<><Header title='Outubro: aproximação de Altamira' sub='01–15/10/2026 • período parcial'/><Map zoom={z} layer={z<.15?'mes-2026-10.png':null} labels={z>.96}/><Side><Tag>03 / MUDANÇA DE ESCALA</Tag><T size={48} style={{fontWeight:700}}>Da Amazônia<br/>a Altamira.</T><T size={52} color={C.orange} style={{marginTop:24,fontWeight:700}}>{n(D.monthly['2026-10'])}</T><T size={25}>detecções na Amazônia Legal<br/>em outubro, até o corte</T><Legend/><T size={22} color={C.muted} style={{marginTop:22}}>Altamira + os cinco vizinhos com maior contagem no período.</T></Side></>;}
  else if(f<2160){const i=Math.min(14,Math.floor((f-1260)/60));const day=days[i];content=<><Header title='Altamira e os cinco vizinhos em destaque' sub='NOAA-20 • detecções diárias • 01–15 de outubro de 2026'/><Map zoom={1} region layer={`dia-${day}.png`} labels/><Side><Tag>04 / DIA A DIA</Tag><T size={54} style={{fontWeight:700}}>{String(i+1).padStart(2,'0')} OUT <span style={{color:C.muted}}>2026</span></T><T size={23} color={i===14?C.gold:C.muted} style={{marginTop:12}}>{i===14?'PARCIAL • corte às 18h40':'00h–24h • horário de Brasília'}</T><T size={82} color={C.orange} style={{fontWeight:700,marginTop:24}}>{n(D.daily[day])}</T><T size={25}>detecções nos seis municípios</T><DailyChart index={i}/><Legend/></Side></>;}
  else if(f<2550){content=<><Header title='Onde os focos se concentram' sub='Acumulado de 01–15/10/2026 • dia 15 parcial • NOAA-20'/><Map zoom={1} region layer='acumulado.png' labels/><Side><Tag>05 / COMPARAÇÃO REGIONAL</Tag><T size={39} style={{fontWeight:700}}>Altamira e vizinhos</T><T size={23} color={C.muted} style={{marginTop:16}}>Maiores contagens entre os municípios que fazem divisa com Altamira.</T><div style={{marginTop:30}}>{D.rank.map(r=><div key={r.code} style={{marginBottom:24}}><div style={{display:'flex',justifyContent:'space-between'}}><T size={25} color={r.code==='1500602'?C.gold:C.white}>{r.name}</T><T size={25}>{n(r.count)}</T></div><div style={{height:10,background:'#29434d',marginTop:10,borderRadius:5}}><div style={{height:10,width:`${r.count/D.rank[0].count*100}%`,background:r.code==='1500602'?C.gold:C.cyan,borderRadius:5}}/></div></div>)}</div><T size={23} color={C.muted} style={{marginTop:22}}>Agora o mapa mostra o acumulado.<br/>Contagens absolutas, sem ajuste por área.</T></Side></>;}
  else if(f<2760){const max=Math.max(...Object.values(D.daily));const peak=days.find(d=>D.daily[d]===max);content=<><Header title='Síntese da observação regional' sub={`01–15/10/2026 • corte: ${D.cutoff} • Brasília`}/><Map zoom={1} region layer='acumulado.png' labels/><Side><Tag>06 / O PERÍODO EM NÚMEROS</Tag><T size={89} color={C.orange} style={{fontWeight:700}}>{n(D.total)}</T><T size={30}>detecções nos seis municípios</T><div style={{marginTop:40,paddingTop:28,borderTop:'1px solid #37505a'}}><T size={24} color={C.muted}>Maior contagem diária</T><T size={42} style={{fontWeight:700,marginTop:12}}>{peak.slice(-2)} de outubro</T><T size={30} color={C.cyan} style={{marginTop:12}}>{n(max)} detecções</T></div><div style={{marginTop:40,paddingTop:28,borderTop:'1px solid #37505a'}}><T size={25}>15 camadas diárias distintas.</T><T size={24} color={C.muted} style={{marginTop:22}}>Uma mesma área pode ser detectada em dias diferentes.</T><T size={24} color={C.muted} style={{marginTop:22}}>Ausência de pontos não comprova ausência de fogo.</T></div></Side></>;}
  else content=<Credits/>;
  return <AbsoluteFill style={{background:C.bg,color:C.white,fontFamily:'Arial, Helvetica, sans-serif'}}>{content}<div style={{position:'absolute',left:46,bottom:23,right:46,display:'flex',justifyContent:'space-between',fontSize:19,color:C.muted}}><span>INPE / Programa Queimadas • NOAA-20 • limites IBGE 2024</span><span>Focos ≠ incêndios únicos • outubro parcial</span></div><div style={{position:'absolute',bottom:0,left:0,height:5,width:`${f/2999*100}%`,background:C.cyan}}/></AbsoluteFill>;
}

export function ATMShortVideo(){
  const f=useCurrentFrame();
  let content;
  if(f<120) {
    content=<Opening frame={f}/>;
  } else if(f<1020) {
    const i=Math.min(9,Math.floor((f-120)/90));
    content=<><Header title='Focos de calor na Amazônia - 2026'/><Map layer={`mes-${monthKeys[i]}.png`} allMunicipios/><Side><T size={54} style={{fontWeight:700}}>{monthNames[i]} - 2026</T><SourceNote/></Side></>;
  } else if(f<1200) {
    const z=interpolate(f,[1020,1185],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)});
    content=<><Header title='Primeira quinzena de outubro de 2026 · Região de Altamira-Pará'/><Map zoom={z} layer={z<.12?'mes-2026-10.png':null} allMunicipios labels={z>.92}/><Side><SourceNote/></Side></>;
  } else if(f<2100) {
    const i=Math.min(14,Math.floor((f-1200)/60));const day=days[i];
    content=<><Header title='Primeira quinzena de outubro de 2026 · Região de Altamira-Pará'/><Map zoom={1} region layer={`dia-${day}.png`} labels/><Side><T size={54} style={{fontWeight:700}}>{String(i+1).padStart(2,'0')} OUT 2026</T><T size={82} color={C.orange} style={{fontWeight:700,marginTop:34}}>{n(D.daily[day])}</T><T size={25}>detecções nos seis municípios</T><DailyChart index={i}/><SourceNote/></Side></>;
  } else if(f<2340) {
    content=<><Header title='Primeira quinzena de outubro de 2026 · Região de Altamira-Pará'/><Map zoom={1} region layer='acumulado.png' labels/><Side><T size={84} color={C.orange} style={{fontWeight:700}}>{n(D.total)}</T><T size={28}>detecções nos seis municípios</T><T size={24} color={C.muted} style={{marginTop:42}}>Acumulado de 01–15/10.<br/>Dia 15 parcial.</T><SourceNote/></Side></>;
  } else {
    content=<Credits/>;
  }
  return <AbsoluteFill style={{background:C.bg,color:C.white,fontFamily:'Arial, Helvetica, sans-serif'}}>{content}<div style={{position:'absolute',left:46,bottom:23,right:46,display:'flex',justifyContent:'space-between',fontSize:19,color:C.muted}}><span>INPE / Programa Queimadas • NOAA-20 • limites IBGE 2024</span><span>Focos ≠ incêndios únicos • outubro parcial</span></div><div style={{position:'absolute',bottom:0,left:0,height:5,width:`${f/2699*100}%`,background:C.cyan}}/></AbsoluteFill>;
}
