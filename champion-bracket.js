(function(){
"use strict";
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels=['النهائي','نصف النهائي','ربع النهائي','دور الـ16','دور الـ32'];
function roundName(index,total){
 const fromEnd=total-1-index;
 return labels[fromEnd] || ('الدور '+(index+1));
}
const matchStatuses={ready:'جاهزة',pending:'بانتظار المتأهل',live:'جارية الآن',finished:'انتهت',bye:'تأهل تلقائي'};
function card(match,interactive){
 if(!match)return '';
 const text=(name,cls)=>'<div class="fixture-team '+cls+'" title="'+escape(name||'')+'"><span>'+escape(name||'بانتظار المتأهل')+'</span></div>';
 const a=match.a||'',b=match.b||'';
 const s=matchStatuses[match.status]||'بانتظار المتأهل';
 const score=match.scores||[];
 const one=score.find(x=>x.name===a),two=score.find(x=>x.name===b);
 return '<div class="match-card '+escape(match.status||'pending')+(interactive?' interactive':'')+'" tabindex="'+(interactive?'0':'-1')+'" '+(interactive?'role="button" aria-label="تفاصيل مواجهة '+escape(a)+' و'+escape(b)+'" data-match="'+escape(match.id)+'"':'')+'>'+
  '<div class="fixture-num"><span>'+escape(match.id.toUpperCase())+'</span><span>'+escape(s)+'</span></div>'+
  text(a,match.winner===a?'winner':'')+
  '<div class="fixture-vs">'+(one&&two?escape(String(one.average))+' — '+escape(String(two.average))+' متوسط النقاط':'VS')+'</div>'+
  text(b,match.winner===b?'winner':'')+'</div>';
}
function wing(rounds,left,interactive){
 if(rounds.length<2)return '';
 const columns=rounds.slice(0,-1);
 return '<div class="wing '+(left?'left':'right')+'">'+columns.map((r,i)=>{
  const half=r.matches.length/2;
  const fixtures=left?r.matches.slice(0,half):r.matches.slice(half);
  return '<div class="round-col" data-ct-round="${i}"><div class="round-title">'+escape(roundName(i,rounds.length))+'</div><div class="fixtures">'+fixtures.map(m=>card(m,interactive)).join('')+'</div></div>';
 }).join('')+'</div>';
}
function render(t,interactive=false){
 const rounds=t?.rounds||[];
 if(!rounds.length)return '<div class="bracket-empty">لا يوجد جدول تصفيات لعرضه.</div>';
 const final=rounds[rounds.length-1].matches[0];
 return '<div class="bracket" aria-label="جدول المواجهات بنظام خروج المغلوب">'+
 wing(rounds,true,interactive)+
 '<div class="center-final"><div class="round-title">'+escape(roundName(rounds.length-1,rounds.length))+'</div><div class="cup" aria-hidden="true"><img class="ct-trophy-img" src="/assets/champion/trophy.svg" alt=""></div>'+
 card(final,interactive)+
 '<div class="champion-name">'+(t.champion?'👑 البطل: '+escape(t.champion):'🏅 بطل البطولة: بانتظار النهائي')+'</div></div>'+
 wing(rounds,false,interactive)+'</div>';
}
function find(t,id){for(const r of t?.rounds||[])for(const m of r.matches)if(m.id===id)return m;return null}

/* Real SVG paths between current match nodes and their next round,
   recalculated from actual element positions. Supports 2–32 participants
   and never overlays/blocks the clickable team cards. */
function drawConnectors(root){
 const canvas=root?.querySelector('.bracket');
 if(!canvas)return;
 canvas.querySelector('.bracket-connector-layer')?.remove();
 const box=canvas.getBoundingClientRect();
 const width=Math.max(1,Math.ceil(canvas.scrollWidth)),height=Math.max(1,Math.ceil(canvas.scrollHeight));
 const paths=[];
 const pos=(el)=>{const r=el.getBoundingClientRect();return{x:r.left-box.left,y:r.top-box.top,width:r.width,height:r.height}};
 const final=canvas.querySelector('.center-final .match-card');
 if(!final)return;
 for(const side of ['left','right']){
  const wing=canvas.querySelector('.wing.'+side);
  if(!wing)continue;
  const cols=[...wing.querySelectorAll('.round-col')];
  cols.forEach((col,i)=>{
   const cards=[...col.querySelectorAll('.match-card')];
   const next=i+1<cols.length
     ?[...cols[i+1].querySelectorAll('.match-card')]:[final];
   cards.forEach((card,index)=>{
    const target=next[Math.floor(index/2)]||next[0];
    if(!target)return;
    const from=pos(card),to=pos(target);
    const x1=side==='left'?from.x+from.width:from.x;
    const x2=side==='left'?to.x:to.x+to.width;
    const mid=x1+(x2-x1)*.53;
    const y1=from.y+from.height/2,y2=to.y+to.height/2;
    if(!Number.isFinite(mid)||!Number.isFinite(y2))return;
    paths.push('M'+x1.toFixed(1)+' '+y1.toFixed(1)+' H'+mid.toFixed(1)+
      ' V'+y2.toFixed(1)+' H'+x2.toFixed(1));
   });
  });
 }
 if(!paths.length)return;
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 svg.setAttribute('class','bracket-connector-layer');
 svg.setAttribute('viewBox','0 0 '+width+' '+height);
 svg.setAttribute('aria-hidden','true');
 svg.style.width=width+'px';svg.style.height=height+'px';
 for(const path of paths){
  const p=document.createElementNS('http://www.w3.org/2000/svg','path');
  p.setAttribute('d',path);svg.appendChild(p);
 }
 canvas.prepend(svg);
}
function afterRender(root){
 requestAnimationFrame(()=>drawConnectors(root));
}
window.addEventListener('resize',()=>{
 for(const root of document.querySelectorAll('.bracket-viewport'))afterRender(root);
},{passive:true});
window.TAGChampionBracket={render,find,escape,roundName,matchStatuses,drawConnectors,afterRender};
})();
