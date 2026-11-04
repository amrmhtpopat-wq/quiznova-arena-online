(async()=>{
  const tk=localStorage.getItem('qn9_teacher_token');if(!tk){location.replace('/');return}
  try{
    const authHeader={'Authorization':'Bearer '+tk};
    const [me,snap]=await Promise.all([fetch('/api/auth/me',{headers:authHeader}),fetch('/api/teacher/snapshot',{headers:authHeader})]);
    if(!me.ok||!snap.ok)throw Error('login_required');
    const m=await me.json(), s=await snap.json();if(!m.ok||!s.ok)throw Error('login_required');
    window.QN9_TEACHER=m.teacher; window.QN9_TOKEN=tk;
    const teacherName=document.getElementById('studioTeacherName'),teacherSubject=document.getElementById('studioTeacherSubject');
    if(teacherName)teacherName.textContent=m.teacher.name;if(teacherSubject)teacherSubject.textContent=m.teacher.subject;
    const prefix='qn9_'+m.teacher.id+'_';
    for(const k of ['quizzes','bank','settings','results'])localStorage.setItem(prefix+k,JSON.stringify(s.data[k]??(k==='settings'?{}:[])));
    let debounce=null;
    window.QN9_ONCHANGE=()=>{clearTimeout(debounce);debounce=setTimeout(async()=>{
      const snapshot={};for(const k of ['quizzes','bank','settings','results']){try{snapshot[k]=JSON.parse(localStorage.getItem(prefix+k)||'null')}catch{}}
      try{const r=await fetch('/api/teacher/snapshot',{method:'POST',headers:{...authHeader,'Content-Type':'application/json'},body:JSON.stringify(snapshot)});if(!r.ok){console.warn('فشل حفظ QuizNova: '+r.status);if(window.toast)window.toast('⚠️ تعذر حفظ التغييرات على الخادم')}}catch(e){console.warn('تعذّر المزامنة مع الخادم',e)}
    },900)};
    window.QN9_KEY=k=>prefix+k;
    const originalFetch=window.fetch.bind(window);
    window.fetch=(input,init={})=>{
      const u=typeof input==='string'?input:(input&&input.url)||'';
      if(u.startsWith('/api/room/start')){init={...init,headers:{...(init.headers||{}),Authorization:'Bearer '+tk}}}
      return originalFetch(input,init);
    };
    document.documentElement.style.visibility='visible';
    let script=document.createElement('script');script.src='/app.js?v=10.0';script.onload=()=>{const view=location.hash.slice(1);if(view&&window.go)window.go(['dashboard','generator','builder','bank','media','library','live','play','results','settings'].includes(view)?view:'dashboard')};document.body.appendChild(script);
  }catch(e){localStorage.removeItem('qn9_teacher_token');location.replace('/')}
})();
