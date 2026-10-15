import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame} from 'remotion';
import data from './dados.json';

const C = {bg:'#071c24',panel:'rgba(4,25,33,.94)',white:'#f4f5ed',muted:'#b8c7c9',cyan:'#63d9d7',coral:'#ff764e',gold:'#ffe492'};
const days=Object.keys(data.contagens);
const number=(value)=>new Intl.NumberFormat('pt-BR').format(value);
const pct=(value)=>value.toFixed(1).replace('.',',')+'%';
const image=(src,opacity=1)=> <Img src={staticFile(src)} style={{width:1920,height:1080,position:'absolute',inset:0,opacity}} />;

const Text=({children,size=28,color=C.white,weight=400,style={}})=><div style={{fontSize:size,color,fontWeight:weight,lineHeight:1.13,...style}}>{children}</div>;
const Panel=({children,left=36,top=180,width=460,height=800,style={}})=><div style={{position:'absolute',left,top,width,height,padding:28,boxSizing:'border-box',borderRadius:20,background:C.panel,...style}}>{children}</div>;

function Header({title,section}){
  return <div style={{position:'absolute',left:36,top:30,width:1848,height:120,borderRadius:20,background:C.panel,display:'flex',alignItems:'center',justifyContent:'space-between',padding:'0 30px',boxSizing:'border-box'}}>
    <div><Text size={21} color={C.cyan} weight={700}>PULSO / AMAZÔNIA</Text><Text size={42} weight={700} style={{marginTop:9}}>{title}</Text></div>
    <div style={{textAlign:'right'}}><Text size={27} color={C.gold} weight={700}>ALTAMIRA · PARÁ</Text><Text size={22} color={C.muted} style={{marginTop:9}}>{section}</Text></div>
  </div>;
}

function Footer({frame,testMode}){
  const duration=testMode?180:1800;
  return <>
    <div style={{position:'absolute',left:0,top:1015,width:1920,height:65,background:C.bg,padding:'8px 38px',boxSizing:'border-box'}}>
      <Text size={19} color={C.muted}>Focos e risco: INPE · Limites: IBGE 2024 · Cena: CesiumJS · Relevo: Esri World Elevation</Text>
      <Text size={19} color={C.muted}>Fundo: Esri, Vantor, Earthstar Geographics e GIS User Community — mosaico de datas diversas</Text>
    </div>
    <div style={{position:'absolute',left:0,top:1076,width:1920,height:4,background:C.cyan,transformOrigin:'left',transform:`scaleX(${(frame+1)/duration})`}} />
  </>;
}

function Intro({frame}){
  const opacity=interpolate(frame,[0,16],[0,1],{extrapolateRight:'clamp'});
  return <>
    <OffthreadVideo src={staticFile('sobrevoo.mp4')} muted style={{width:1920,height:1080,objectFit:'cover'}} />
    <Header title="Da Amazônia a Altamira" section="LOCALIZAÇÃO" />
    <Panel height={295} style={{opacity}}>
      <Text size={26} color={C.cyan} weight={700}>08–14 OUTUBRO 2026</Text>
      <Text size={44} weight={700} style={{marginTop:28}}>Altamira, Pará</Text>
      <Text size={26} color={C.gold} style={{marginTop:34}}>Limite municipal em amarelo</Text>
      <Text size={24} color={C.muted} style={{marginTop:14}}>Municípios vizinhos em linhas discretas</Text>
    </Panel>
  </>;
}

function Daily({frame,testMode}){
  const local=testMode?frame:frame-240;
  const index=testMode?6:Math.min(6,Math.floor(local/720*7));
  const day=days[index];
  const onset=testMode?0:240+Math.ceil(index*720/7);
  const fade=interpolate(frame,[onset,onset+11],[.2,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
  const max=Math.max(...Object.values(data.contagens));
  return <>
    {image('paisagem.jpg')}
    {!testMode&&days.slice(0,index).map(d=><React.Fragment key={d}>{image(`anteriores-${d}.png`)}</React.Fragment>)}
    {image(`focos-${day}.png`,fade)}
    <Header title="Sete dias de detecções" section="08–14 OUT 2026" />
    <Panel width={460}>
      <Text size={24} color={C.cyan} weight={700}>{testMode?'TESTE VISUAL':`DIA ${index+1} DE 7`}</Text>
      <Text size={40} weight={700} style={{marginTop:24}}>{day.slice(8)} OUT 2026</Text>
      <Text size={24} color={C.muted} style={{marginTop:12}}>00h–24h · Brasília (UTC−3)</Text>
      <Text size={76} color={C.coral} weight={700} style={{marginTop:40}}>{number(data.contagens[day])}</Text>
      <Text size={27}>detecções neste dia</Text>
      <Text size={23} color={C.cyan} weight={700} style={{marginTop:48,marginBottom:18}}>EVOLUÇÃO DIÁRIA</Text>
      {days.map((d,j)=><div key={d} style={{display:'flex',alignItems:'center',gap:12,height:43}}>
        <Text size={22} color={j===index?C.white:C.muted}>{d.slice(8)}</Text>
        <div style={{width:210,height:21,borderRadius:5,background:C.bg}}><div style={{width:`${100*data.contagens[d]/max}%`,height:'100%',borderRadius:5,background:j===index?C.coral:'#3c5963'}} /></div>
        <Text size={22} color={j===index?C.white:C.muted}>{number(data.contagens[d])}</Text>
      </div>)}
      <Text size={23} color={C.muted} style={{position:'absolute',bottom:38}}>Focos não são incêndios únicos.</Text>
    </Panel>
    <Text size={27} color={C.gold} weight={700} style={{position:'absolute',left:988,top:452}}>ALTAMIRA</Text>
    <Text size={28} weight={700} style={{position:'absolute',left:1555,top:210}}>N ↑</Text>
    <Panel left={1390} top={760} width={494} height={235}>
      <Text size={22} color={C.gold} weight={700}>COMO LER</Text>
      <Text size={25} style={{marginTop:18}}><span style={{color:C.coral}}>●</span> Detecções do dia</Text>
      {testMode?<Text size={23} color={C.muted} style={{marginTop:17}}>Somente 14 de outubro</Text>:<><Text size={25} style={{marginTop:16}}><span style={{color:'#7a9ea8'}}>●</span> Dias anteriores</Text><Text size={22} color={C.muted} style={{marginTop:12}}>Atenuação visual ≠ extinção</Text></>}
      <Text size={22} color={C.muted} style={{marginTop:11}}>Pontos sem escala de área</Text>
    </Panel>
  </>;
}

function Risk(){
  return <>
    {image('paisagem.jpg')}{image('risco.png')}
    <Header title="O contexto ambiental" section="RISCO DE FOGO" />
    <Panel width={485}>
      <Text size={24} color={C.cyan} weight={700}>VARIÁVEL MODELADA</Text>
      <Text size={42} weight={700} style={{marginTop:30}}>Risco de fogo</Text>
      <Text size={71} color={C.coral} weight={700} style={{marginTop:34}}>{pct(data.riscoCobertura)}</Text>
      <Text size={26}>dos registros têm valor válido</Text>
      <Text size={26} style={{marginTop:28}}>08–14 de outubro de 2026</Text>
      <Text size={25} color={C.muted} style={{marginTop:50}}>A cor indica o índice associado a cada detecção do período.</Text>
      <Text size={25} color={C.muted} style={{marginTop:38}}>Não representa a cobertura contínua de todo o município.</Text>
      <Text size={24} color={C.muted} style={{marginTop:38}}>Não é previsão de incêndios nem medida de área queimada.</Text>
      <Text size={22} color={C.cyan} style={{position:'absolute',bottom:38}}>Fonte: campos ambientais do INPE</Text>
    </Panel>
    <Panel left={1390} top={760} width={494} height={235}>
      <Text size={23} color={C.gold} weight={700}>COMO LER</Text>
      <div style={{height:24,marginTop:25,background:'linear-gradient(90deg,#50c2c2,#ff6242)'}} />
      <div style={{display:'flex',justifyContent:'space-between',marginTop:6}}><Text size={22}>0</Text><Text size={22}>1</Text></div>
      <Text size={24} style={{marginTop:12}}>Índice modelado nos focos</Text>
      <Text size={22} color={C.muted} style={{marginTop:8}}>Cinza: dado indisponível</Text>
    </Panel>
  </>;
}

function Distribution(){
  return <>
    {image('paisagem.jpg')}{image('distribuicao.png')}
    <Header title="Onde as detecções se concentram" section="DISTRIBUIÇÃO" />
    <Panel width={485}>
      <Text size={24} color={C.cyan} weight={700}>08–14 OUT · BRASÍLIA</Text>
      <Text size={72} color={C.coral} weight={700} style={{marginTop:38}}>{number(data.total)}</Text>
      <Text size={28}>detecções no período</Text>
      <Text size={63} weight={700} style={{marginTop:54}}>{pct(data.oeste54)}</Text>
      <Text size={25}>a oeste do meridiano 54° O</Text>
      <Text size={25} color={C.muted} style={{marginTop:50}}>Uma mesma área pode aparecer em várias passagens de satélites.</Text>
      <Text size={25} color={C.muted} style={{marginTop:45}}>Imagens recentes avaliadas: nuvens e lacunas limitam a visão.</Text>
      <Text size={25} color={C.muted} style={{marginTop:45}}>O fundo é um mosaico histórico; os pontos são observações recentes.</Text>
    </Panel>
  </>;
}

function Summary(){
  return <>
    <AbsoluteFill style={{backgroundImage:`url(${staticFile('paisagem.jpg')})`,backgroundSize:'cover',filter:'brightness(.26)'}} />
    <Header title="Altamira | síntese do período" section="08–14 OUT 2026" />
    <div style={{position:'absolute',left:82,top:205,width:1600}}>
      <Text size={114} color={C.coral} weight={700}>{number(data.total)}</Text>
      <Text size={35}>detecções · 7 dias completos · múltiplos satélites</Text>
      <Text size={31} style={{marginTop:48}}>Maior contagem diária: 8 de outubro · {number(Math.max(...Object.values(data.contagens)))} detecções</Text>
      <div style={{marginTop:65}}><Text size={29}>Focos e contexto ambiental: INPE / Programa Queimadas</Text><Text size={29} style={{marginTop:15}}>Limite municipal e vizinhos: IBGE / Amazônia Legal 2024</Text><Text size={29} style={{marginTop:15}}>Visualização: Remotion + CesiumJS / Esri World Imagery / World Elevation</Text></div>
      <div style={{marginTop:56}}><Text size={28} color={C.muted}>Datas e horários em Brasília (UTC−3). Sem narração.</Text><Text size={28} color={C.muted} style={{marginTop:15}}>Detecção não equivale a incêndio único ou área queimada.</Text><Text size={28} color={C.muted} style={{marginTop:15}}>Ausência de pontos não comprova ausência de fogo.</Text><Text size={28} color={C.muted} style={{marginTop:55}}>Camadas, fontes e limitações acompanham esta edição.</Text></div>
    </div>
  </>;
}

export const AltamiraVideo=({testMode})=>{
  const frame=useCurrentFrame();
  let content;
  if(testMode) content=<Daily frame={frame} testMode />;
  else if(frame<240) content=<Intro frame={frame} />;
  else if(frame<960) content=<Daily frame={frame} testMode={false} />;
  else if(frame<1320) content=<Risk />;
  else if(frame<1560) content=<Distribution />;
  else content=<Summary />;
  return <AbsoluteFill style={{fontFamily:'Arial, Helvetica, sans-serif',background:C.bg,color:C.white,overflow:'hidden'}}>{content}<Footer frame={frame} testMode={testMode} /></AbsoluteFill>;
};
