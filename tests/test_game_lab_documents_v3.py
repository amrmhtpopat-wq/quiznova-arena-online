"""Document parser smoke tests for the actual PDF and Word textbook upload formats."""
import io
import unittest
import os
import tempfile
import atexit
from pathlib import Path
DOC_TEMP=tempfile.TemporaryDirectory()
atexit.register(DOC_TEMP.cleanup)
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(DOC_TEMP.name)/'docparser.sqlite')
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store
platform_store.init()

from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

import game_lab_pro as lab


class DocumentParsers(unittest.TestCase):
    def test_real_docx_extracts_paragraphs_and_tables(self):
        doc=Document()
        doc.add_heading('Computer technology',level=1)
        doc.add_paragraph('CPU: The main processing unit that executes instructions.')
        doc.add_paragraph('RAM: A temporary memory used while applications are active.')
        table=doc.add_table(rows=1,cols=2)
        table.cell(0,0).text='Keyboard'
        table.cell(0,1).text='Input device'
        data=io.BytesIO()
        doc.save(data)
        pages=lab.docx_pages(data.getvalue())
        self.assertGreater(len(pages),0)
        joined=' '.join(p['text'] for p in pages)
        self.assertIn('CPU',joined)
        self.assertIn('RAM',joined)
        self.assertIn('Keyboard',joined)
        self.assertIn('Input device',joined)

    def test_real_pdf_extracts_text(self):
        writer=PdfWriter()
        page=writer.add_blank_page(width=595,height=842)
        font=DictionaryObject({
            NameObject('/Type'):NameObject('/Font'),
            NameObject('/Subtype'):NameObject('/Type1'),
            NameObject('/BaseFont'):NameObject('/Helvetica')
        })
        font_ref=writer._add_object(font)
        page[NameObject('/Resources')]=DictionaryObject({
            NameObject('/Font'):DictionaryObject({NameObject('/F1'):font_ref})
        })
        content=DecodedStreamObject()
        lines=[
           'CPU: Processing instructions and performing operations.',
           'RAM: Temporary working memory for loaded programs.',
           'Monitor: A device that presents text and images.'
        ]
        stream='BT /F1 12 Tf 45 770 Td 15 TL '
        for line in lines:
            stream+='('+line+') Tj T* '
        stream+='ET'
        content.set_data(stream.encode('latin-1'))
        page[NameObject('/Contents')]=writer._add_object(content)
        buffer=io.BytesIO()
        writer.write(buffer)
        pages=lab.pdf_pages(buffer.getvalue())
        self.assertEqual(len(pages),1)
        self.assertIn('CPU',pages[0]['text'])
        self.assertIn('RAM',pages[0]['text'])
        self.assertIn('Monitor',pages[0]['text'])

    def test_definition_extraction_remains_source_bound(self):
        src='''[صفحة 7]
وحدة المعالجة: تنفذ العمليات الحسابية والمنطقية في جهاز الحاسوب.
[صفحة 8]
ذاكرة الوصول: تحفظ البيانات المؤقتة عند تشغيل البرامج.'''
        rows=lab.deterministic_draft(src,10)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['sourcePage'],7)
        self.assertEqual(rows[1]['sourcePage'],8)
        self.assertIn('وحدة المعالجة',rows[0]['q'])


if __name__=='__main__':unittest.main(verbosity=2)
