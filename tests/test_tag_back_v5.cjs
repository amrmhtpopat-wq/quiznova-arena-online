/* TAG V5 release gate: every root HTML page has one back strategy and site logo is current. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readdirSync('.').filter(p=>p.endsWith('.html')&&!p.includes('.fragment.'));
const excluded=['index.html','pwa-offline.html'];
let count=0;
for(const file of html){
 const s=fs.readFileSync(file,'utf8');
 if(file==='pwa-offline.html')assert.match(s,/tag-offline-back/,file+' needs offline link');
 else if(file==='index.html'){
  assert.match(s,/tag-entry-spatial-v5\.css/,file+' missing new dark public landing');
  assert.match(s,/tag-back-nav-v5\.js/,file+' missing native teacher back action');
  assert.match(s,/tag-spatial-identity-v3\.webp/,file+' missing current logo');
 }else{
  assert.match(s,/tag-back-nav-v5\.css/,file+' missing back styling');
  assert.match(s,/tag-back-nav-v5\.js/,file+' missing functional back navigation');
 }
 if(file.startsWith('champion')){
  assert.match(s,/<img class="brand-img" src="\/assets\/brand\/tag-spatial-identity-v3\.webp"/,file+' uses outdated logo');
  assert.match(s,/tag-champion-logo-v5\.css/,file+' lacks scoped logo sizing');
  assert.doesNotMatch(s,/tag-entry-spatial-v5\.css/,file+' must preserve game branding');
 }
 if(file.startsWith('tag-lab-')||file.startsWith('game-lab-'))
  assert.doesNotMatch(s,/tag-entry-spatial-v5\.css/,file+' must preserve TAG LAB');
 count++;
}
const js=fs.readFileSync('tag-back-nav-v5.js','utf8');
assert.doesNotThrow(()=>new vm.Script(js));
assert.match(js,/previous\.origin===location\.origin/);
assert.match(js,/history\.back\(\)/);
assert.match(js,/location\.assign\(fallback\(\)\)/);
assert.doesNotMatch(js,/localStorage\.clear|sessionStorage\.clear|fetch\(['"]\/api\/students/);
const css=fs.readFileSync('tag-entry-spatial-v5.css','utf8');
assert.match(css,/prefers-reduced-motion/);
assert.match(css,/@media\(max-width:620px\)/);
assert.match(css,/#studentWelcome \.bo-entry-option/);
const resp=fs.readFileSync('tag-responsive-site-v5.css','utf8');
assert.match(resp,/@media print/);
assert.match(resp,/@media\(max-width:650px\)/);
console.log('PASS TAG V5: '+count+' HTML pages, responsive controls, safe fallback, current championship logos and unchanged LAB styling.');
