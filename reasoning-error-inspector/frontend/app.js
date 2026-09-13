const $ = (id) => document.getElementById(id);
let ready = false, busy = false, reportId = null, sourceName = null;
function node(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
function error(message) { $('error').textContent = message; $('error').hidden = !message; }
function controls() { $('analyze-button').disabled = !ready || busy; $('document').disabled = busy; }
async function responseJSON(response) { const data = await response.json(); if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : data.detail?.message || 'The request could not be completed.'); return data; }
async function health() {
  try {
    const data = await responseJSON(await fetch('/api/health'));
    ready = data.status === 'ready'; $('status').textContent = ready ? `Model ready · ${data.device.toUpperCase()}` : data.status === 'loading' ? 'Loading model…' : 'Setup needs attention';
    $('status').className = `status ${ready ? 'ready' : data.status === 'error' ? 'failed' : ''}`;
    if (data.model_name) $('model-name').textContent = data.model_name;
    if (ready) $('model-details').textContent = `Block ${data.layer} · threshold ${data.threshold.toFixed(2)} · same checkpoint for generation and probing`;
    $('setup-message').hidden = !data.message; $('setup-message').textContent = data.message || '';
    controls(); if (data.status === 'loading') setTimeout(health, 4000);
  } catch (_) { $('status').textContent = 'Backend unavailable'; $('setup-message').hidden = false; $('setup-message').textContent = 'Start the FastAPI backend and reload this page.'; }
}
$('context').addEventListener('input', () => { $('character-count').textContent = `${$('context').value.length.toLocaleString()} characters`; });
$('document').addEventListener('change', async () => {
  const file = $('document').files[0]; if (!file) return;
  if (file.size > 10 * 1024 * 1024) { error('Choose a document smaller than 10 MB.'); return; }
  error(''); busy = true; controls(); $('source-name').textContent = 'Extracting document text…';
  try { const form = new FormData(); form.append('file', file); const data = await responseJSON(await fetch('/api/documents', {method:'POST', body:form})); $('context').value = data.text; sourceName = data.name; $('source-name').textContent = `${data.name} · ${data.characters.toLocaleString()} characters`; $('context').dispatchEvent(new Event('input')); }
  catch (e) { error(e.message); $('source-name').textContent = 'Upload failed; pasted text is unchanged'; }
  finally { busy = false; controls(); $('document').value = ''; }
});
function chart(rows, threshold, highest) {
  const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns,'svg');
  const width=560, left=56, right=45, top=22, rowHeight=35, plotWidth=width-left-right, height=top+rows.length*rowHeight+30;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`); svg.setAttribute('role','img'); svg.setAttribute('aria-label',`Hop error scores with threshold ${threshold.toFixed(2)}`); svg.classList.add('score-chart');
  function shape(type, attrs, text) { const n=document.createElementNS(ns,type); Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v))); if(text!==undefined)n.textContent=text;svg.append(n);return n; }
  rows.forEach((r,i)=>{const y=top+i*rowHeight;shape('text',{x:0,y:y+16,fill:'#607087','font-size':12},`Hop ${r.index}`);shape('rect',{x:left,y,width:plotWidth,height:22,rx:4,fill:'#f0f3f8'});shape('rect',{x:left,y,width:Math.max(1,r.error_score*plotWidth),height:22,rx:4,fill:r.index===highest?'#2855e8':r.flagged?'#c78f3d':'#c5d2ed'});shape('text',{x:width-34,y:y+16,fill:'#38506d','font-size':12},r.error_score.toFixed(2));});
  const x=left+threshold*plotWidth;shape('line',{x1:x,x2:x,y1:top-5,y2:height-29,stroke:'#263954','stroke-dasharray':'4 4','stroke-width':1.5});shape('text',{x:Math.min(Math.max(x,90),width-100),y:height-9,fill:'#607087','font-size':11,'text-anchor':'middle'},`Threshold ${threshold.toFixed(2)}`);return svg;
}
function render(data) {
  const target=$('results'); target.replaceChildren(); target.hidden=false; $('empty').hidden=true; reportId=data.report_id; $('download').hidden=false;
  target.append(node('div','ANALYZED QUESTION','small-label'),node('p',data.question,'result-summary'));
  const answer=node('div',undefined,'answer-box');answer.append(node('span','GENERATED ANSWER','small-label'),node('p',data.answer));if(data.answer_note)answer.append(node('div',data.answer_note,'muted'));target.append(answer);
  if(data.controlled_error){const c=data.controlled_error,box=node('div',undefined,'demo-result');box.append(node('h3','CONTROLLED TEST ERROR'),node('div',`A test edit was inserted at Hop ${c.hop_index}: ${c.original_value} → ${c.replacement_value}.`),node('div',`Highest-scoring hop: ${data.most_suspicious_hop}. ${c.correct_localization?'The probe localized the edited hop.':'The probe did not localize the edited hop.'}`),node('div','This is an injected test, not a naturally occurring model error.','muted'));target.append(box);}
  const summary=data.first_flagged_hop===null?'No reasoning hop crossed the learned error threshold.':`First threshold crossing: Hop ${data.first_flagged_hop}. This is a candidate error location.`;
  target.append(node('div','PROBE LOCALIZATION','small-label'),node('p',summary,'result-summary'));
  const metrics=node('div',undefined,'metrics');for(const [label,value] of [['HIGHEST-SCORING',`Hop ${data.most_suspicious_hop}`],['HOPS ANALYZED',data.hops.length],['THRESHOLD',data.threshold.toFixed(2)]]){const m=node('div',undefined,'metric');m.append(node('span',label,'small-label'),node('strong',String(value)));metrics.append(m);}target.append(metrics,chart(data.hops,data.threshold,data.most_suspicious_hop));
  for(const h of data.hops){const card=node('article',undefined,`hop-card ${h.index===data.most_suspicious_hop?'highest':''} ${h.flagged?'flagged':''}`),top=node('div',undefined,'hop-top');top.append(node('strong',`Hop ${h.index}`));if(h.index===data.most_suspicious_hop)top.append(node('span','HIGHEST SCORE','pill'));top.append(node('span',h.flagged?'FLAGGED':'Not flagged',h.flagged?'pill amber':'hop-score'));card.append(top,node('p',h.text),node('span',`Probe error score: ${h.error_score.toFixed(3)}`,'hop-score'));target.append(card);}
  const e=data.evidence_analysis,panel=node('section',undefined,'evidence');panel.append(node('span','SEPARATE EVIDENCE CHECK','small-label'),node('h3',e.status==='CONTRADICTED'?'Possible factual discrepancy':e.status==='SUPPORTED'?'Evidence supports this claim':'Not enough information to verify'));
  panel.append(node('p',`Examining Hop ${data.most_suspicious_hop}. This evidence assessment is separate from the hidden-state probe.`, 'muted'));
  const dl=node('dl');for(const [label,value] of [['Claim',e.claim],['Claimed',e.claimed_value],['Reference',e.supported_value]])if(value)dl.append(node('dt',label),node('dd',value));panel.append(dl);if(e.evidence)panel.append(node('blockquote',e.evidence));panel.append(node('p',e.explanation,'muted'));target.append(panel);
  const details=node('details',undefined,'reference-details');details.append(node('summary',data.retrieval.used?`Evidence excerpts used · ${data.reference_source}`:`Reference used · ${data.reference_source}`),node('p',data.retrieval.used?'Only the displayed retrieved excerpts were analyzed; omitted text was not checked.':'The full supplied reference was analyzed.'),node('pre',data.reference_context));target.append(details);
  for(const warning of data.warnings||[])target.append(node('p',warning,'muted'));
}
$('analyze-form').addEventListener('submit', async event => {
  event.preventDefault(); if(busy||!ready)return;error('');busy=true;controls();$('activity').hidden=false;
  const started=Date.now();const timer=setInterval(()=>$('activity-text').textContent=`Generating and analyzing… ${Math.floor((Date.now()-started)/1000)}s`,1000);
  try{const data=await responseJSON(await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:$('question').value,context:$('context').value,inject_test_error:$('demo').checked,source_name:sourceName})}));render(data);}
  catch(e){error(e.message);}finally{clearInterval(timer);busy=false;controls();$('activity').hidden=true;$('activity-text').textContent='Generating and analyzing…';}
});
$('download').addEventListener('click',async()=>{if(!reportId)return;try{const res=await fetch(`/api/reports/${reportId}.pdf`);if(!res.ok){await responseJSON(res);return;}const url=URL.createObjectURL(await res.blob());const a=node('a');a.href=url;a.download='reasoning-diagnostic.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){error(e.message);}});
health();
