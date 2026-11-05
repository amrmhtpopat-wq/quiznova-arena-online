#!/usr/bin/env python3
"""One-time safe, all-or-nothing migration from V9 SQLite to an EMPTY Neon PostgreSQL project.
Dry run: python MIGRATE_LOCAL_TO_NEON.py --source quiznova_local.db
Apply:   DATABASE_URL is set by the user, then python MIGRATE_LOCAL_TO_NEON.py --source ... --apply
Do not upload the SQLite file or DATABASE_URL publicly.
"""
import argparse, os, sqlite3, sys
from pathlib import Path

TABLES = ['teachers','datasets','students','played_sessions','student_attempts']

def main():
    ap=argparse.ArgumentParser(description='QuizNova V10 secure migration to an EMPTY Neon PostgreSQL database')
    ap.add_argument('--source', default='quiznova_local.db', help='Path to the original V9/V9.3 SQLite database')
    ap.add_argument('--apply', action='store_true', help='Perform migration; default is preview only')
    args=ap.parse_args()
    path=Path(args.source).expanduser().resolve()
    if not path.is_file():raise SystemExit('The SQLite source file does not exist. Check --source path.')
    sql=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
    sql.row_factory=sqlite3.Row
    counts={}
    for tbl in TABLES:
        try:counts[tbl]=sql.execute('SELECT COUNT(*) FROM '+tbl).fetchone()[0]
        except sqlite3.OperationalError:counts[tbl]=0
    print('LOCAL SOURCE:',path.name,'\nRECORD COUNTS:')
    for table,count in counts.items():print('  ',table,count)
    if not args.apply:
        print('\nDry run only. To import, provide DATABASE_URL securely and add --apply.')
        return
    url=os.getenv('DATABASE_URL','')
    if not url.lower().startswith(('postgresql://','postgres://')):
        raise SystemExit('DATABASE_URL must be a PostgreSQL connection URI in the environment.')
    try:
        import psycopg
    except ImportError:
        raise SystemExit('Install dependencies first: pip install -r requirements.txt')
    # Initializes the V10 database schema with the same production code; does not migrate old sessions.
    import platform_store
    if platform_store.DATABASE_KIND!='postgres':raise SystemExit('Cloud destination not configured')
    platform_store.init()
    with psycopg.connect(url) as dest:
        with dest.transaction():
            for table in TABLES:
                with dest.cursor() as cur:
                    cur.execute('SELECT COUNT(*) FROM '+table)
                    existing=int(cur.fetchone()[0])
                    if existing:
                        raise RuntimeError('Destination is NOT EMPTY: '+table+' has '+str(existing)+' rows. Migration cancelled.')
            for table in TABLES:
                if not counts[table]:continue
                rows=[dict(x) for x in sql.execute('SELECT * FROM '+table)]
                if table=='teachers':
                    for row in rows:
                        row['school_type']=row.get('school_type') or platform_store.inferred_school_type(row.get('school',''))
                if not rows:continue
                fields=list(rows[0])
                cols=','.join('"'+f+'"' for f in fields)
                marks=','.join(['%s']*len(fields))
                statement=f'INSERT INTO {table}({cols}) VALUES({marks})'
                with dest.cursor() as cur:
                    cur.executemany(statement, [[r.get(c) for c in fields] for r in rows])
                print('Imported',table,len(rows))
        print('Migration completed in ONE database transaction. Existing account passwords remain hashed.')
        print('IMPORTANT: Sign in with the SAME teacher email/password as the local V9 version.')
        print('Live rooms and login sessions were intentionally not imported.')
    sql.close()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('MIGRATION FAILED (transaction rolled back):',type(exc).__name__,str(exc),file=sys.stderr)
        sys.exit(1)
