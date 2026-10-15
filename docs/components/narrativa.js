globalThis.PulsoNarrative = function() {
  const steps=[...document.querySelectorAll('.story-step')],reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const button=document.getElementById('story-toggle');let enabled=!reduced.matches;
  function activate(element) {
    steps.forEach(s=>s.classList.toggle('is-active',s===element));
    const mode=element.dataset.story;
    document.getElementById('history-experience').dataset.focus=mode;
    document.getElementById('story-caption').textContent=element.querySelector('h3').textContent;
  }
  steps.forEach(s=>s.querySelector('button').onclick=()=>activate(s));
  const label=()=>{button.textContent=enabled?'Pausar narrativa guiada':'Ativar narrativa guiada';button.setAttribute('aria-pressed',String(enabled));};
  button.onclick=()=>{enabled=!enabled;label();};label();
  reduced.addEventListener('change',()=>{if(reduced.matches){enabled=false;label();}});
  if(globalThis.scrollama)scrollama().setup({step:'.story-step',offset:.6}).onStepEnter(({element})=>{if(enabled)activate(element);});
};
