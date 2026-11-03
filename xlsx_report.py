"""Generate a compact, right-to-left formatted Excel (.xlsx) classroom report with stdlib only."""
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
from datetime import datetime, timezone, timedelta

JORDAN = timezone(timedelta(hours=3))

def col(n):
    s=''
    while n:
        n,r=divmod(n-1,26);s=chr(65+r)+s
    return s

def cell(r,c,value,style=3):
    ref=f'{col(c)}{r}'
    if value is None: value=''
    if isinstance(value,(float,int)) and not isinstance(value,bool):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    v=escape(str(value),{'"':'&quot;'})
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{v}</t></is></c>'

def sheet_xml(rows,widths,merges=None,filter_range=None,freeze_row=0,highlight_rows=None):
    merges=merges or []
    cols=''.join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i,w in enumerate(widths,1))
    output=[]
    highlight_rows=highlight_rows or set()
    for ri, (values,sty) in enumerate(rows,1):
        if sty=='title': ids=[1]*len(values);h=37
        elif sty=='subtitle': ids=[2]*len(values);h=29
        elif sty=='header': ids=[4]*len(values);h=31
        elif sty=='kpi': ids=[5]+[6]*(len(values)-1);h=34
        elif sty=='section': ids=[7]*len(values);h=29
        else: ids=[3 if ri%2 else 8]*len(values);h=26
        if ri in highlight_rows: ids=[9]*len(values)
        output.append(f'<row r="{ri}" ht="{h}" customHeight="1">'+''.join(cell(ri,ci,v,ids[ci-1]) for ci,v in enumerate(values,1))+'</row>')
    frz=f'<pane ySplit="{freeze_row}" topLeftCell="A{freeze_row+1}" activePane="bottomLeft" state="frozen"/>' if freeze_row else ''
    mrg=f'<mergeCells count="{len(merges)}">'+''.join(f'<mergeCell ref="{m}"/>' for m in merges)+'</mergeCells>' if merges else ''
    autof=f'<autoFilter ref="{filter_range}"/>' if filter_range else ''
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
      '<sheetViews><sheetView workbookViewId="0" rightToLeft="1" showGridLines="0">'+frz+'</sheetView></sheetViews>'
      '<sheetFormatPr defaultRowHeight="24"/><cols>'+cols+'</cols><sheetData>'+''.join(output)+'</sheetData>'+mrg+autof+'</worksheet>')

def generate_report(room, students, questions):
    dt=datetime.fromtimestamp((room.get('finishedAt') or room.get('createdAt') or 0)/1000, JORDAN)
    date=dt.strftime('%Y-%m-%d'); clock=dt.strftime('%H:%M')
    graded=sum(1 for q in room['quiz']['questions'] if q.get('type')!='poll')
    all_correct=sum(p['correct'] for p in students)
    all_wrong=sum(p['wrong'] for p in students)
    total_attempts=graded*len(students)
    grade=round(all_correct*100/total_attempts,1) if total_attempts else 0
    section=room.get('section') or 'غير محددة'
    title=room['quiz'].get('title','')
    mode='مجموعات' if room.get('playType')=='teams' else 'فردي'
    summary=[
      (['QUIZNOVA ARENA | تقرير الشعبة','','','','',''],'title'),
      (['نتائج المسابقة الصفية • المهارات الرقمية','','','','',''],'subtitle'),
      (['الشعبة',section,'عنوان الاختبار',title,'رمز الجلسة',room['code']],'kpi'),
      (['التاريخ',date,'الوقت',clock,'طريقة اللعب',mode],'kpi'),
      (['التقييم العام / 100',grade,'عدد الطلاب',len(students),'عدد الأسئلة المقوّمة',graded],'kpi'),
      (['الإجابات الصحيحة',all_correct,'الإجابات الخاطئة',all_wrong,'بدون إجابة',max(0,total_attempts-all_correct-all_wrong)],'kpi'),
      (['','', '', '', '', ''],'normal'),
      (['مؤشرات وتفسير النتائج','','','','',''],'section'),
      (['التقييم من 100 يساوي نسبة الإجابات الصحيحة لجميع الطلاب إلى إجمالي الأسئلة المقوّمة × الطلاب.','','','','',''],'normal'),
      (['الأسئلة المتروكة أو التي انتهى وقتها تُحسب دون إجابة ولا تُعتبر صحيحة.','','','','',''],'normal'),
      (['النتيجة', 'ممتاز' if grade>=90 else 'جيد جدًا' if grade>=80 else 'جيد' if grade>=65 else 'يحتاج دعم','','','',''],'kpi'),
      (['إعداد: QuizNova Arena • تقرير آلي من جلسة الاختبار','','','','',''],'subtitle')]
    detail=[(['QUIZNOVA ARENA | نتائج الطلاب']+['']*9,'title'),
       (['الشعبة: '+section+'  |  التاريخ: '+date+'  |  تقييم الشعبة: '+str(grade)+'/100']+['']*9,'subtitle'),
       (['','']+['']*8,'normal'),
       (['الترتيب','اسم الطالب','الشعبة','الفريق','النموذج','الصحيحة','الخاطئة','دون إجابة','التقييم / 100','النقاط'],'header')]
    for i,p in enumerate(students,1):
        detail.append(([i,p['name'],section,p.get('team') or '—',p.get('model') or '—',p['correct'],p['wrong'],p.get('unanswered',max(0,graded-p['correct']-p['wrong'])),p['percent'],p['score']],'normal'))
    analysis=[(['QUIZNOVA ARENA | تحليل الأسئلة']+['']*7,'title'),
       (['الشعبة: '+section+'  |  التاريخ: '+date]+['']*7,'subtitle'),
       (['']*8,'normal'),
       (['#','نص السؤال','الإجابة الصحيحة','الدقة / 100','إجابات صحيحة','إجابات خاطئة','بدون إجابة','المرجع'],'header')]
    for i,q in enumerate(questions,1):
        analysis.append(([i,q.get('text',''),q.get('correctAnswer',''),q.get('accuracy',0),len(q.get('correctStudents',[])),len(q.get('wrongStudents',[])),len(q.get('skippedStudents',[])),(q.get('source','')+' - ص '+str(q.get('sourcePage',''))) if q.get('source') else '—'],'normal'))
    sheets=[('ملخص الشعبة',sheet_xml(summary,[25,24,24,43,24,30],['A1:F1','A2:F2','A8:F8','A9:F9','A10:F10','A12:F12'])),
            ('نتائج الطلاب',sheet_xml(detail,[11,32,23,25,13,15,15,17,19,19],['A1:J1','A2:J2'],f'A4:J{max(4,len(detail))}',4)),
            ('تحليل الأسئلة',sheet_xml(analysis,[10,70,40,16,18,19,18,52],['A1:H1','A2:H2'],f'A4:H{max(4,len(analysis))}',4))]
    main='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    style='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="4"><font><sz val="11"/><name val="Arial"/><color rgb="FF162E50"/></font><font><b/><sz val="19"/><name val="Arial"/><color rgb="FFFFFFFF"/></font><font><b/><sz val="12"/><name val="Arial"/><color rgb="FF0E3F66"/></font><font><b/><sz val="11"/><name val="Arial"/><color rgb="FFFFFFFF"/></font></fonts>
<fills count="8"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF075F99"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFBDEFFF"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FF138FC4"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFE5F9FF"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF1FAFF"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFCCF3FF"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="hair"><color rgb="FFCEECF6"/></left><right style="hair"><color rgb="FFCEECF6"/></right><top style="hair"><color rgb="FFCEECF6"/></top><bottom style="hair"><color rgb="FFCEECF6"/></bottom><diagonal/></border></borders>
<cellStyleXfs count="1"><xf fontId="0" fillId="0" borderId="0" numFmtId="0"/></cellStyleXfs>
<cellXfs count="10"><xf fontId="0" fillId="0" borderId="0" xfId="0"/><xf fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf><xf fontId="2" fillId="3" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf><xf fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf><xf fontId="3" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf><xf fontId="2" fillId="5" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf><xf fontId="2" fillId="6" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf><xf fontId="2" fillId="3" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf><xf fontId="0" fillId="6" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf><xf fontId="2" fillId="7" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf></cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''
    wb='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><bookViews><workbookView/></bookViews><sheets>'''+''.join(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i,(name,_) in enumerate(sheets,1))+'</sheets></workbook>'
    rel='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'''+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+'<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
    types='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'''+''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1))+'</Types>'
    out=BytesIO()
    with ZipFile(out,'w',ZIP_DEFLATED) as f:
        f.writestr('[Content_Types].xml',types)
        f.writestr('_rels/.rels','''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>''')
        f.writestr('xl/workbook.xml',wb);f.writestr('xl/_rels/workbook.xml.rels',rel);f.writestr('xl/styles.xml',style)
        for i,(_,xml) in enumerate(sheets,1): f.writestr(f'xl/worksheets/sheet{i}.xml',xml)
    return out.getvalue()
