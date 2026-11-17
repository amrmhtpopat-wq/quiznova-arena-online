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
  return '<div class="round-col"><div class="round-title">'+escape(roundName(i,rounds.length))+'</div><div class="fixtures">'+fixtures.map(m=>card(m,interactive)).join('')+'</div></div>';
 }).join('')+'</div>';
}
function render(t,interactive=false){
 const rounds=t?.rounds||[];
 if(!rounds.length)return '<div class="bracket-empty">لا يوجد جدول تصفيات لعرضه.</div>';
 const final=rounds[rounds.length-1].matches[0];
 return '<div class="bracket" aria-label="جدول المواجهات بنظام خروج المغلوب">'+
 wing(rounds,true,interactive)+
 '<div class="center-final"><div class="round-title">'+escape(roundName(rounds.length-1,rounds.length))+'</div><div class="cup" aria-hidden="true">🏆</div>'+
 card(final,interactive)+
 '<div class="champion-name">'+(t.champion?'👑 البطل: '+escape(t.champion):'🏅 بطل البطولة: بانتظار النهائي')+'</div></div>'+
 wing(rounds,false,interactive)+'</div>';
}
function find(t,id){for(const r of t?.rounds||[])for(const m of r.matches)if(m.id===id)return m;return null}
window.TAGChampionBracket={render,find,escape,roundName,matchStatuses};
})();
