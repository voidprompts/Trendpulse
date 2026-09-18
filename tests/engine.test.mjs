import fs from 'fs';
const html=fs.readFileSync('index.html','utf8');
const src=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).find(b=>b.includes('jsonpRequest'));
if(!src) throw new Error('engine not found');
const patched0=src.replace("els.form.addEventListener('submit', generate);","")
 .replace("els.copy.addEventListener('click', copyOutput);","")
 .replace(/Array\.prototype\.forEach[\s\S]*?\}\);\s*\}\);/,"")
 ;
const _i=patched0.lastIndexOf("})();");
const patched=patched0.slice(0,_i)+"globalThis.T={toCamelCase,toPhrase,buildTags,stripStopWords,parseSuggestions,dedupe,fallbackPhrases,normalize};})();"+patched0.slice(_i+5);
const el=()=>({classList:{add(){},remove(){}},addEventListener(){},style:{},dataset:{},value:'',textContent:'',innerHTML:'',setAttribute(){},getAttribute(){}});
globalThis.document={getElementById:el,querySelectorAll:()=>[],createElement:el,head:{appendChild(){}},body:{appendChild(){},removeChild(){}}};
globalThis.window={setTimeout,clearTimeout};
(0,eval)(patched);
const T=globalThis.T;
let p=0,f=0;
const eq=(n,g,w)=>{const ok=JSON.stringify(g)===JSON.stringify(w);ok?p++:f++;console.log(`${ok?'PASS':'FAIL'} ${n}`);if(!ok)console.log(`   got:  ${JSON.stringify(g)}\n   want: ${JSON.stringify(w)}`);};

console.log('--- parse real autocomplete envelope ---');
// Exact payload shape documented for client=youtube
const real=["faded",[["faded",0,[433]],["faded alan walker lyrics",0,[433]],["faded remix",0,[433]],["faded 8d",0,[433]]],{"k":1,"q":"_sPyvXmm"}];
eq('extracts phrases',T.parseSuggestions(real),["faded","faded alan walker lyrics","faded remix","faded 8d"]);
try{T.parseSuggestions(["q",[]]);console.log('FAIL empty rejected');f++;}catch(e){console.log('PASS empty rejected ('+e.message+')');p++;}
try{T.parseSuggestions({bad:1});console.log('FAIL shape rejected');f++;}catch(e){console.log('PASS bad shape rejected ('+e.message+')');p++;}

console.log('\n--- stop word stripping ---');
eq('leading stopwords',T.stripStopWords('how to do the griddy'),['griddy']);
eq('interior kept',T.stripStopWords('cat vs dog fight'),['cat','vs','dog','fight']);
eq('interior phrase intact',T.toCamelCase('cat vs dog fight'),'CatVsDogFight');
eq('trailing stopwords',T.stripStopWords('sigma edit is'),['sigma','edit']);

console.log('\n--- camelCase (IG/FB) ---');
eq('camelCase basic',T.toCamelCase('trending audio meme'),'TrendingAudioMeme');
eq('camelCase strips stopwords',T.toCamelCase('how to do the griddy'),'Griddy');
eq('camelCase accents',T.toCamelCase('café münster edit'),'CafeMunsterEdit');
eq('camelCase punctuation',T.toCamelCase("mr beast's $1 video!"),'MrBeastS1Video');

console.log('\n--- YouTube phrases ---');
eq('phrase lowercase spaced',T.toPhrase('Trending Audio Meme'),'trending audio meme');
eq('phrase no hash',T.toPhrase('AI & robots').includes('#'),false);

console.log('\n--- velocity: hourly/daily get fast modifiers ---');
const ph=['skibidi toilet','skibidi edit'];
const h=T.buildTags('skibidi',ph,'hourly','instagram').text;
const d=T.buildTags('skibidi',ph,'daily','instagram').text;
const w=T.buildTags('skibidi',ph,'weekly','instagram').text;
const mo=T.buildTags('skibidi',ph,'monthly','instagram').text;
console.log('hourly :',h);
console.log('weekly :',w);
eq('hourly has #shorts',h.includes('#shorts'),true);
eq('hourly has #reels',h.includes('#reels'),true);
eq('hourly has #viral',h.includes('#viral'),true);
eq('daily has #shorts',d.includes('#shorts'),true);
eq('weekly NO #shorts',w.includes('#shorts'),false);
eq('monthly NO #viral',mo.includes('#viral'),false);

console.log('\n--- platform formats ---');
const ig=T.buildTags('griddy',ph,'daily','instagram');
eq('IG every token hashed',ig.text.split(' ').every(t=>t.startsWith('#')),true);
eq('IG no spaces inside tags',/^#\S+( #\S+)*$/.test(ig.text),true);
const yt=T.buildTags('griddy',ph,'daily','youtube');
console.log('YT:',yt.text);
eq('YT commas',yt.text.includes(', '),true);
eq('YT no hash',yt.text.includes('#'),false);
eq('YT <=500',yt.text.length<=500,true);
const all=T.buildTags('griddy',ph,'daily','all').text;
eq('all-platform mixes amps',all.includes('#reels')&&all.includes('#shorts')&&all.includes('#fyp'),true);

console.log('\n--- dedupe & caps ---');
const dup=T.buildTags('shorts',['shorts','shorts','Shorts'],'hourly','instagram').text.split(' ');
eq('case-insensitive dedupe',dup.length===new Set(dup.map(x=>x.toLowerCase())).size,true);
const many=Array.from({length:60},(_,i)=>'very long trending phrase number '+i);
const big=T.buildTags('kw',many,'hourly','youtube');
eq('YT capped <=500',big.text.length<=500,true);
console.log('   YT len',big.text.length);
const bigIg=T.buildTags('kw',many,'hourly','instagram');
eq('IG tag cap <=24',bigIg.count<=24,true);

console.log('\n--- unicode preservation (regression) ---');
eq('japanese kept',T.toCamelCase('アニメ 2026'),'アニメ2026');
eq('cyrillic kept',T.toCamelCase('мем видео'),'МемВидео');
eq('emoji stripped',T.toCamelCase('cat 😂 meme'),'CatMeme');
eq('latin accents folded',T.toCamelCase('café münster'),'CafeMunster');
eq('no empty hashtag',T.buildTags('アニメ',['アニメ edit'],'hourly','instagram').text.includes('# '),false);

console.log('\n--- fallback ---');
const fb=T.fallbackPhrases('drone');
eq('fallback 10',fb.length,10);
const fbOut=T.buildTags('drone',fb,'hourly','instagram');
eq('fallback usable',fbOut.count>5,true);
console.log('   ',fbOut.text);

console.log(`\n${p} passed, ${f} failed`);
process.exit(f?1:0);
