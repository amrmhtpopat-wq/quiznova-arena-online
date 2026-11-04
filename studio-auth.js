(async()=>{
  const tk=localStorage.getItem('qn9_teacher_token');if(!tk){location.replace('/');return}
  try{
    const authHeader={'Authorization':'Bearer '+tk};
    const [me,snap]=await Promise.all([fetch('/api/auth/me',{headers:authHeader}),fetch('/api/teacher/snapshot',{headers:authHeader})]);
    if(!me.ok||!snap.ok)throw Error('login_required');
    const m=await me.json(), s=await snap.json();if(!m.ok||!s.ok)throw Error('login_required');
    window.QN9_TEACHER=m.teacher; window.QN9_TOKEN=tk;
    let revision=Number(s.revision||0),baseline=JSON.parse(JSON.stringify(s.data));
    const teacherName=document.getElementById('studioTeacherName'),teacherSubject=document.getElementById('studioTeacherSubject');
    if(teacherName)teacherName.textContent=m.teacher.name;if(teacherSubject)teacherSubject.textContent=m.teacher.subject;
    const prefix='qn9_'+m.teacher.id+'_';
    const keys=['quizzes','bank','settings','results'];
    const pendingKey=prefix+'pending_conflict';
    const pending=localStorage.getItem(pendingKey);
    for(const k of keys)localStorage.setItem(prefix+k,JSON.stringify(s.data[k]??(k==='settings'?{}:[])));
    function keepDraft(patch){localStorage.setItem(pendingKey,JSON.stringify({date:new Date().toISOString(),patch}));}
    function downloadDraft(){const txt=localStorage.getItem(pendingKey);if(!txt)return;const link=document.createElement('a');const url=URL.createObjectURL(new Blob([txt],{type:'application/json'}));link.href=url;link.download='QuizNova_unsynced_changes.json';link.click();URL.revokeObjectURL(url)}
    if(pending&&confirm('هناك تعديلات محلية من جلسة سابقة لم يتم حفظها في السحابة. هل تريد تنزيل نسخة احتياطية منها؟'))downloadDraft();
    let debounce=null;const dirty=new Set();let saving=false;
    const readLocal=k=>{try{return JSON.parse(localStorage.getItem(prefix+k)||'null')}catch{return null}};
    const warn=message=>{console.warn(message);if(window.toast)window.toast(message)};
    function queueSave(){clearTimeout(debounce);debounce=setTimeout(flush,700)}
    async function flush(){
      if(saving||!dirty.size)return;
      saving=true;
      const changed=keys.filter(k=>dirty.has(k));
      const patch=Object.fromEntries(changed.map(k=>[k,readLocal(k)]));
      try{
        let r=await fetch('/api/teacher/snapshot',{method:'POST',headers:{...authHeader,'Content-Type':'application/json'},body:JSON.stringify({revision,patch})});
        if(r.status===409){
          const fresh=await fetch('/api/teacher/snapshot',{headers:authHeader,cache:'no-store'});
          if(!fresh.ok)throw Error('conflict_refresh_failed');
          const remote=await fresh.json();
          const clashes=changed.filter(k=>JSON.stringify(remote.data[k])!==JSON.stringify(baseline[k]));
          if(clashes.length){keepDraft(patch);warn('⚠️ تعارض بين جهازين. حفظنا نسخة آمنة من تعديلاتك محليًا؛ لن نستبدل بيانات السحابة.');return}
          for(const k of keys)if(!dirty.has(k))localStorage.setItem(prefix+k,JSON.stringify(remote.data[k]));
          baseline=JSON.parse(JSON.stringify(remote.data));revision=remote.revision;
          r=await fetch('/api/teacher/snapshot',{method:'POST',headers:{...authHeader,'Content-Type':'application/json'},body:JSON.stringify({revision,patch})});
        }
        if(!r.ok)throw Error('save_failed_'+r.status);
        const answer=await r.json();revision=answer.revision;
        for(const k of changed)if(JSON.stringify(readLocal(k))===JSON.stringify(patch[k])){dirty.delete(k);baseline[k]=patch[k]}
        if(!dirty.size)localStorage.removeItem(pendingKey);
      }catch(e){keepDraft(patch);warn('⚠️ تعذر الحفظ على الخادم. محفوظة نسخة من التعديلات في المتصفح.')}
      finally{saving=false;if(dirty.size&&navigator.onLine!==false){}}
    }
    window.QN9_ONCHANGE=field=>{if(field&&keys.includes(field))dirty.add(field);else keys.forEach(k=>dirty.add(k));queueSave()};
    window.addEventListener('online',()=>{if(dirty.size)queueSave()});
    window.QN9_KEY=k=>prefix+k;
    const originalFetch=window.fetch.bind(window);
    window.fetch=(input,init={})=>{
      const u=typeof input==='string'?input:(input&&input.url)||'';
      if(u.startsWith('/api/room/start')){init={...init,headers:{...(init.headers||{}),Authorization:'Bearer '+tk}}}
      return originalFetch(input,init);
    };
    document.documentElement.style.visibility='visible';
    let script=document.createElement('script');script.src='/app.js?v=10.3';script.onload=()=>{const view=location.hash.slice(1);if(view&&window.go)window.go(['dashboard','generator','builder','bank','media','library','live','play','results','settings'].includes(view)?view:'dashboard')};document.body.appendChild(script);
  }catch(e){localStorage.removeItem('qn9_teacher_token');location.replace('/')}
})();
