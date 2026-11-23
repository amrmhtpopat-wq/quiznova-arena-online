/* TAG Spatial V3 rollout guard. Run with node tests/test_tag_spatial_sitewide_v3.cjs */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const approved=['index.html','studio.html','student.html','stage.html','app.html','about.html','for-teachers.html','admin.html'];
const excluded=['champion.html','tag-lab-home.html','game-lab-preview.html'];
const css=fs.readFileSync('tag-spatial-site-v3.css','utf8');
const js=fs.readFileSync('tag-spatial-site-v3.js','utf8');
const palette=fs.readFileSync('tag-spatial-unify-v4.css','utf8');
const hub=fs.readFileSync('tag-spatial-home-v3.html','utf8');
const native=fs.readFileSync('tag-spatial-native-v3.js','utf8');
const nativeCss=fs.readFileSync('tag-spatial-native-v3.css','utf8');
const fragment=fs.readFileSync('tag-spatial-native-v3.fragment.html','utf8');
assert.doesNotThrow(()=>new vm.Script(js));
assert.ok(css.includes('body.tag-spatial-global'));
assert.match(css,/@media print/);
assert.match(css,/prefers-reduced-motion/);
assert.match(palette,/#workspace\.hidden\{display:none!important\}/,'login wall must remain isolated');
assert.match(palette,/tag-spatial-v4-fallback/,'legacy fallback required');
assert.doesNotThrow(()=>new vm.Script(native));
assert.ok(!js.includes("createElement('iframe')"),'site theme must not create iframe');
assert.ok(!native.includes("createElement('iframe')"),'native workspace must not create iframe');
assert.ok(js.includes("attachShadow({mode:'open'})"),'teacher home Shadow DOM required');
assert.ok(native.includes("getContext('webgl'"),'approved WebGL scene missing');
assert.ok(native.includes('TAGSpatialNativeInit'),'native initializer missing');
assert.match(nativeCss,/:host\s*\{/,'isolated stylesheet missing');
assert.ok(fragment.includes('data-tool="create"'),'native dashboard markup missing');
assert.ok(native.includes('window.location.assign(next.href)'),'single click routing required');
assert.ok(!native.match(/function openItem\(key\)\{[\s\S]{0,1000}inspector\.classList\.add\('open'\)/),'tool details modal should not open');
assert.match(js,/if\(excluded\.test\(here\)/);
assert.ok(!js.includes('localStorage.clear()'));
assert.ok(!js.includes('deleteStudent'));
assert.ok(!js.includes('fetch("/api'));
for(const file of approved){
 const html=fs.readFileSync(file,'utf8');
 assert.ok(html.includes('class="tag-spatial-global'),file+' missing opt-in');
 assert.ok(html.includes('/tag-spatial-site-v3.css?v=3'),file+' missing stylesheet');
 assert.ok(html.includes('/tag-spatial-site-v3.js?v=3'),file+' missing JS');
 assert.ok(html.includes('/tag-spatial-unify-v4.css?v=4.1'),file+' missing final palette');
 assert.ok(!html.includes('TAG_QUIZ_DELETE_ALL'),'unexpected destructive token');
}
for(const file of excluded){
 if(!fs.existsSync(file))continue;
 const html=fs.readFileSync(file,'utf8');
 assert.ok(!html.includes('tag-spatial-site-v3.css'),file+' must be excluded');
 assert.ok(!html.includes('tag-spatial-site-v3.js'),file+' must be excluded');
}
for(const part of ['data-tool="create"','data-tool="ai"','data-tool="library"','data-tool="lab"',
 'data-tool="cards"','data-tool="live"','data-tool="champ"','data-tool="results"','data-tool="settings"']){
 assert.ok(hub.includes(part),'missing teacher tool '+part);
}
assert.ok(fs.readFileSync('index.html','utf8').includes('/tag-spatial-native-v3.js?v=3'),'native portal initializer missing');
assert.ok(!fs.readFileSync('index.html','utf8').includes('<script defer src="/tag-spatial-direct-v3.js'),'obsolete direct renderer loaded');
assert.ok(fragment.includes('data-tool='),'native dashboard markup missing');
assert.ok(hub.includes('location.origin'),'same origin links absent');
assert.ok(hub.includes('tag-spatial-identity-v3.webp'),'new logo path not in prototype');
assert.ok(fs.readFileSync('portal.js','utf8').includes('function go(name)'));
assert.ok(fs.readFileSync('app.js','utf8').includes('function go(view'));
console.log('PASS TAG Spatial V3: 8 themed pages, 9 destinations, native 3D ShadowRoot integration, QA exclusions, original app handlers.');
