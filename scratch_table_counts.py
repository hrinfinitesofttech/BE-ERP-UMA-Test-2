import sqlite3

conn = sqlite3.connect('live_pa_db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'django_%' AND name NOT LIKE 'auth_%'")
tables = [r[0] for r in cur.fetchall()]
for t in sorted(tables):
    try:
        cnt = cur.execute(f"SELECT COUNT(1) FROM {t}").fetchone()[0]
        if cnt > 0:
            print(f"{t}: {cnt}")
    except Exception as e:
        pass
