import fs from 'fs';
const html=fs.readFileSync('index.html','utf8');
const src=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(b=>b.includes('jsonpRequest'));
const patched0=src.replace("els.form.addEventListener('submit', generate);","")
 .replace("els.copy.addEventListener('click', copyOutput);","")
 .replace(/Array\.prototype\.forEach[\s\S]*?\}\);\s*\}\);/,"")
 ;
const _i=patched0.lastIndexOf("})();");
const patched=patched0.slice(0,_i)+"globalThis.T={fetchSuggestions,jsonpRequest,buildTags,fallbackPhrases};})();"+patched0.slice(_i+5);

// ---- Simulate the browser's script-injection behaviour ----
// document.head.appendChild(script) -> resolve src, eval the JSONP body.
let injected=[];
let mode='ok';
function makeScript(){
  const o={_src:'',async:false,onerror:null,parentNode:null,
    set src(v){this._src=v;queueMicrotask(()=>run(o,v));},get src(){return this._src;}};
  return o;
}
function run(o,url){
  injected.push(url);
  const cb=decodeURIComponent(new URL(url).searchParams.get('jsonp'));
  const q=new URL(url).searchParams.get('q');
  const host=new URL(url).host;
  if(mode==='dead'||(mode==='firstdead'&&host==='suggestqueries.google.com')){
    if(o.onerror)o.onerror(); return;
  }
  if(mode==='hang')return; // never calls back -> timeout path
  // Real envelope: window.google.ac.h([...]) but with our custom callback name
  const body=`${cb}(["${q}",[["${q} edit",0,[433]],["${q} compilation",0,[433]],["how to ${q}",0,[433]],["${q} meme",0,[433]]],{"k":1}])`;
  (0,eval)(body);
}
const el=()=>({classList:{add(){},remove(){}},addEventListener(){},style:{},dataset:{},value:'',textContent:'',innerHTML:'',setAttribute(){},getAttribute(){}});
globalThis.document={getElementById:el,querySelectorAll:()=>[],
  createElement:(t)=>t==='script'?makeScript():el(),
  head:{appendChild(s){/* src setter already scheduled run */}},
  body:{appendChild(){},removeChild(){}}};
globalThis.window=globalThis;
globalThis.setTimeout=setTimeout;globalThis.clearTimeout=clearTimeout;
(0,eval)(patched);
const T=globalThis.T;

console.log('=== 1. happy path: JSONP resolves ===');
injected=[];mode='ok';
let phrases=await T.fetchSuggestions('skibidi');
console.log('URL:',injected[0].replace('https://suggestqueries.google.com/complete/search',''));
console.log('phrases:',phrases);
console.log('client=youtube present:',injected[0].includes('client=youtube'));
console.log('ds=yt present:',injected[0].includes('ds=yt'));
console.log('custom jsonp callback:',/jsonp=__tpAc\d+/.test(injected[0]));

console.log('\n=== 2. callback global cleaned up after use ===');
const leaked=Object.keys(globalThis).filter(k=>k.startsWith('__tpAc'));
console.log('leaked globals:',leaked.length,leaked);

console.log('\n=== 3. first mirror dead -> falls through to second ===');
injected=[];mode='firstdead';
phrases=await T.fetchSuggestions('griddy');
console.log('attempts:',injected.length);
console.log('hosts tried:',injected.map(u=>new URL(u).host));
console.log('recovered:',phrases.length,'phrases');

console.log('\n=== 4. all mirrors dead -> rejects, UI falls back ===');
injected=[];mode='dead';
try{await T.fetchSuggestions('x');console.log('ERROR: should have rejected');}
catch(e){
  console.log('rejected:',e.message);
  const fb=T.buildTags('x',T.fallbackPhrases('x'),'hourly','instagram');
  console.log('fallback string:',fb.count,'tags');
}
console.log('\n=== 5. endpoint hangs -> timeout fires, no leak ===');
injected=[];mode='hang';
const t0=Date.now();
try{await T.fetchSuggestions('hang');console.log('ERROR: should reject');}
catch(e){console.log('rejected after',Math.round((Date.now()-t0)/1000)+'s:',e.message);}
console.log('globals after timeout:',Object.keys(globalThis).filter(k=>k.startsWith('__tpAc')).length);

console.log('\n=== 6. end-to-end output ===');
mode='ok';
const live=await T.fetchSuggestions('skibidi toilet');
for(const [tf,pf] of [['hourly','instagram'],['daily','youtube'],['monthly','all']]){
  const r=T.buildTags('skibidi toilet',live,tf,pf);
  console.log(`${tf}/${pf} (${r.count} tags):`);
  console.log('   '+r.text);
}
