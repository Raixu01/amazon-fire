globalThis.PulsoMunicipio = {
  read(codes) { return FireModel.municipalCode(new URL(location.href).searchParams.get('municipio'),codes); },
  write(code) { const url=new URL(location.href);if(code)url.searchParams.set('municipio',code);else url.searchParams.delete('municipio');globalThis.history.replaceState(null,'',url); },
  render(m,total) {
    const host=document.getElementById('municipal-profile');host.hidden=!m;
    if(!m)return;
    document.getElementById('municipal-name').textContent=`${m.nome} · ${m.uf}`;
    document.getElementById('municipal-summary').textContent=`Código IBGE ${m.codigo_ibge}. ${total==null?'Dados indisponíveis':total.toLocaleString('pt-BR')+' focos no período selecionado'}. Os gráficos e o mapa mostram este município. O endereço do navegador pode ser compartilhado.`;
  }
};
