import fs from 'fs';
const html=fs.readFileSync('index.html','utf8');
const src=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(b=>b.includes('jsonpRequest'));
const patched0=src.replace("els.form.addEventListener('submit', generate);","")
 .replace("els.copy.addEventListener('click', copyOutput);","")
 .replace(/Array\.prototype\.forEach[\s\S]*?\}\);\s*\}\);/,"")
 ;
const _i=patched0.lastIndexOf("})();");
const patched=patched0.slice(0,_i)+"globalThis.T={toCamelCase,toPhrase,buildTags,fallbackPhrases,normalize};})();"+patched0.slice(_i+5);
const el=()=>({classList:{add(){},remove(){}},addEventListener(){},style:{},dataset:{},value:'',textContent:'',innerHTML:'',setAttribute(){},getAttribute(){}});
globalThis.document={getElementById:el,querySelectorAll:()=>[],createElement:el,head:{appendChild(){}},body:{appendChild(){},removeChild(){}}};
globalThis.window=globalThis;
(0,eval)(patched);
const T=globalThis.T;

// Inputs that are plausible from a real user or a real autocomplete response
const cases=[
  ['all stop words',        'how to',            ['how to do the','how to make']],
  ['japanese',              'アニメ',             ['アニメ 2026','アニメ edit']],
  ['emoji only',            '😂😂',              ['😂 meme','😂 edit']],
  ['numbers only',          '2026',              ['2026 recap','2026 trends']],
  ['hyphenated',            'mr-beast',          ['mr-beast challenge']],
  ['very long',             'a'.repeat(120),     ['x edit']],
  ['single letter',         'a',                 ['a edit','a meme']],
  ['punctuation storm',     '!!!???',            ['??? meme']],
];
let problems=0;
for(const [name,kw,sugg] of cases){
  for(const pf of ['instagram','youtube']){
    const r=T.buildTags(kw,sugg,'hourly',pf);
    const toks = pf==='youtube' ? r.text.split(', ') : r.text.split(' ');
    const empty = toks.filter(t=>t===''||t==='#'||t==='#undefined'||/^#?\s*$/.test(t));
    const flag = empty.length?'  <-- EMPTY/BARE TOKEN':'';
    if(empty.length)problems++;
    console.log(`${name.padEnd(18)} ${pf.padEnd(10)} ${r.count} tags${flag}`);
    if(empty.length||name==='japanese'||name==='emoji only'||name==='all stop words')
      console.log(`    ${JSON.stringify(r.text).slice(0,150)}`);
  }
}
console.log('\nproblem cases:',problems);
