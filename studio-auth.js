(async()=>{
  const allowedViews=['dashboard','generator','builder','bank','media','library','live','play','results','settings'];
  const requestedView=location.hash.slice(1);
  const safeView=allowedViews.includes(requestedView)?requestedView:'dashboard';
  const loginTarget='/?next='+encodeURIComponent('/studio.html#'+safeView);
  const tk=localStorage.getItem('qn9_teacher_token');
  if(!tk){location.replace(loginTarget);return}
  try{
    const authHeader={'Authorization':'Bearer '+tk};
    let m=null,s=null,lastStatus=[];
    for(let attempt=0;attempt<3;attempt++){
      try{
        const [me,snap]=await Promise.all([
          fetch('/api/auth/me',{headers:authHeader,cache:'no-store'}),
          fetch('/api/teacher/snapshot',{headers:authHeader,cache:'no-store'})
        ]);
        lastStatus=[me.status,snap.status];
        if(me.ok&&snap.ok){
          const teacherData=await me.json(),snapshotData=await snap.json();
          if(teacherData.ok&&snapshotData.ok){
            m=teacherData;s=snapshotData;break;
          }
        }
      }catch(e){lastStatus=['network','network']}
      if(attempt<2)await new Promise(resolve=>setTimeout(resolve,350*(attempt+1)));
    }
    if(!m||!s){
      // Only both endpoints consistently rejecting an invalid session justify relogin.
      // Mixed 200/401, 429 or 5xx must NOT silently delete a valid teacher session.
      if(lastStatus.length===2&&lastStatus.every(code=>code===401))throw Error('login_required');
      throw Error('temporary_auth_unavailable');
    }
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
    let debounce=null;const dirty=new Set();let savingPromise=null;
    const readLocal=k=>{try{return JSON.parse(localStorage.getItem(prefix+k)||'null')}catch{return null}};
    const warn=message=>{console.warn(message);if(window.toast)window.toast(message)};
    function queueSave(){clearTimeout(debounce);debounce=setTimeout(()=>{void flush()},700)}
    async function commitDirty(){
      if(!dirty.size)return true;
      const changed=keys.filter(k=>dirty.has(k));
      const patch=Object.fromEntries(changed.map(k=>[k,readLocal(k)]));
      try{
        let r=await fetch('/api/teacher/snapshot',{method:'POST',headers:{...authHeader,'Content-Type':'application/json'},body:JSON.stringify({revision,patch})});
        if(r.status===409){
          const fresh=await fetch('/api/teacher/snapshot',{headers:authHeader,cache:'no-store'});
          if(!fresh.ok)throw Error('conflict_refresh_failed');
          const remote=await fresh.json();
          if(!remote.ok)throw Error('conflict_refresh_failed');
          const clashes=changed.filter(k=>JSON.stringify(remote.data[k])!==JSON.stringify(baseline[k]));
          if(clashes.length){
            keepDraft(patch);
            warn('⚠️ تعارض بين جهازين. حفظنا نسخة آمنة من تعديلاتك محليًا؛ لن نستبدل بيانات السحابة.');
            return false;
          }
          for(const k of keys)if(!dirty.has(k))localStorage.setItem(prefix+k,JSON.stringify(remote.data[k]));
          baseline=JSON.parse(JSON.stringify(remote.data));revision=remote.revision;
          r=await fetch('/api/teacher/snapshot',{method:'POST',headers:{...authHeader,'Content-Type':'application/json'},body:JSON.stringify({revision,patch})});
        }
        if(!r.ok)throw Error('save_failed_'+r.status);
        const answer=await r.json();
        if(!answer.ok)throw Error('save_rejected');
        revision=answer.revision;
        for(const k of changed){
          if(JSON.stringify(readLocal(k))===JSON.stringify(patch[k])){
            dirty.delete(k);
            baseline[k]=patch[k];
          }
        }
        if(!dirty.size)localStorage.removeItem(pendingKey);
        return true;
      }catch(e){
        keepDraft(patch);
        warn('⚠️ تعذر الحفظ على الخادم. التعديلات ما زالت موجودة محليًا. حاول الحفظ مجددًا.');
        return false;
      }
    }
    async function flush(){
      clearTimeout(debounce);debounce=null;
      if(savingPromise){
        const previous=await savingPromise;
        if(!previous)return false;
        return dirty.size?flush():true;
      }
      if(!dirty.size)return true;
      savingPromise=commitDirty();
      let ok=false;
      try{ok=await savingPromise;return ok;}
      finally{
        savingPromise=null;
        if(ok&&dirty.size)queueSave();
      }
    }
    window.QN9_SAVE_NOW=()=>flush();
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
    let script=document.createElement('script');script.src='/app.js?v=11.1';script.onload=()=>{const view=location.hash.slice(1);if(view&&window.go)window.go(['dashboard','generator','builder','bank','media','library','live','play','results','settings'].includes(view)?view:'dashboard')};document.body.appendChild(script);
  }catch(e){
    if(e.message==='login_required'){
      localStorage.removeItem('qn9_teacher_token');
      location.replace(loginTarget);
      return;
    }
    // A temporary server problem should never kick the teacher to the dashboard.
    document.documentElement.style.visibility='visible';
    const main=document.querySelector('main')||document.body;
    main.innerHTML='<section style="max-width:650px;margin:12vh auto;padding:30px;border-radius:20px;background:#102e53;border:1px solid #55a7ce;color:#f2faff;font:600 17px/1.8 Cairo,Tahoma,Arial;text-align:center" dir="rtl">'
      +'<h2 style="color:#fff">تعذر التحقق من الجلسة مؤقتًا</h2>'
      +'<p style="color:#d0e9fa">الخادم لم يستجب بشكل ثابت. لم نحذف جلسة المعلم أو بيانات الاختبارات.</p>'
      +'<button id="qnRetryStudio" type="button" style="padding:12px 24px;border:0;border-radius:12px;background:#a5e9f8;color:#092d48;font-weight:900;cursor:pointer">إعادة المحاولة</button> '
      +'<a href="'+loginTarget+'" style="color:#fff;text-decoration:underline;margin-inline:12px">تسجيل الدخول من جديد</a>'
      +'</section>';
    document.querySelector('#qnRetryStudio')?.addEventListener('click',()=>location.reload());
    console.warn('Studio session initialization failed',e.message||e);
  }
})();
