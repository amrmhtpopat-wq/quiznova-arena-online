"""Authenticated, bounded chunked schoolbook uploads for TAG LAB QA.

Uploads are assembled in a private temporary file, then parsed into the
teacher-owned library. Temporary files are removed on finalize/cancel/expiry.
They are deliberately not permanent storage. File uploads are scoped to the
authenticated teacher and capped before any bytes are accepted.
"""
from __future__ import annotations

import base64
import binascii
import os
import secrets
import tempfile
import threading
import time

MAX_BOOK_BYTES=40_000_000
CHUNK_BYTES=1_000_000
SESSION_TTL=30*60
UPLOADS={}
LOCK=threading.RLock()
FORMATS={'pdf','docx','txt'}

def _check_file(filename, length):
    filename=str(filename or '').strip()[:130]
    if not filename or '.' not in filename or filename.rsplit('.',1)[-1].lower() not in FORMATS:
        raise ValueError('unsupported_book_format')
    if isinstance(length,bool):
        raise ValueError('file_too_large')
    try:
        length=int(length)
    except (TypeError,ValueError,OverflowError):
        raise ValueError('file_too_large')
    if not 0<length<=MAX_BOOK_BYTES:
        raise ValueError('file_too_large')
    return filename,length

def _unlink(session):
    try:os.unlink(session['path'])
    except FileNotFoundError:pass

def _expire():
    current=time.time()
    for key,session in list(UPLOADS.items()):
        if current-session['touched']>SESSION_TTL:
            UPLOADS.pop(key,None)
            _unlink(session)

def _session(tid, upload_id):
    session=UPLOADS.get(str(upload_id or ''))
    if not session:
        raise ValueError('upload_not_found')
    if session['teacher_id']!=tid:
        raise ValueError('upload_not_found')
    if time.time()-session['touched']>SESSION_TTL:
        UPLOADS.pop(str(upload_id),None)
        _unlink(session)
        raise ValueError('upload_expired')
    return session

def start(tid, data, book_count):
    filename,size=_check_file(data.get('filename'),data.get('fileSize'))
    if int(book_count)>=12:
        raise ValueError('book_limit')
    section=str(data.get('section') or 'كتاب كامل').strip()[:60]
    with LOCK:
        _expire()
        for key,session in list(UPLOADS.items()):
            if session['teacher_id']==tid:
                UPLOADS.pop(key,None)
                _unlink(session)
        descriptor,path=tempfile.mkstemp(prefix='tag-lab-book-',suffix='.part')
        os.close(descriptor)
        upload_id=secrets.token_urlsafe(24)
        UPLOADS[upload_id]={
            'teacher_id':tid,'path':path,'filename':filename,
            'section':section,'size':size,'uploaded':0,'index':0,'touched':time.time()
        }
    return {'uploadId':upload_id,'chunkBytes':CHUNK_BYTES,'fileSize':size,'maxBytes':MAX_BOOK_BYTES}

def chunk(tid, data):
    upload_id=data.get('uploadId')
    with LOCK:
        session=_session(tid,upload_id)
        index=data.get('index')
        if type(index) is not int or index!=session['index']:
            raise ValueError('upload_chunk_order')
        expected=min(CHUNK_BYTES,session['size']-session['uploaded'])
        if expected<=0:
            raise ValueError('upload_complete')
        encoded=data.get('data')
        if not isinstance(encoded,str) or len(encoded)>(CHUNK_BYTES*4//3)+16:
            raise ValueError('upload_chunk_invalid')
        try:
            raw=base64.b64decode(encoded,validate=True)
        except (ValueError,TypeError,binascii.Error) as exc:
            raise ValueError('upload_chunk_invalid') from exc
        if len(raw)!=expected:
            raise ValueError('upload_chunk_invalid')
        with open(session['path'],'ab') as stream:
            stream.write(raw)
        session['uploaded']+=len(raw)
        session['index']+=1
        session['touched']=time.time()
        return {'uploaded':session['uploaded'],'fileSize':session['size']}

def finish(tid, data, save_callback):
    upload_id=str(data.get('uploadId') or '')
    with LOCK:
        session=_session(tid,upload_id)
        if session['uploaded']!=session['size']:
            raise ValueError('upload_incomplete')
        UPLOADS.pop(upload_id,None)
    try:
        with open(session['path'],'rb') as stream:
            raw=stream.read(MAX_BOOK_BYTES+1)
        if len(raw)!=session['size']:
            raise ValueError('upload_incomplete')
        return save_callback(tid,{'filename':session['filename'],'section':session['section']},raw)
    finally:
        _unlink(session)

def cancel(tid, data):
    upload_id=str(data.get('uploadId') or '')
    with LOCK:
        session=_session(tid,upload_id)
        UPLOADS.pop(upload_id,None)
        _unlink(session)
    return {'cancelled':True}
