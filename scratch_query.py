import sqlite3

conn = sqlite3.connect('live_pa_db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT id, lead_no, company_name, product_name, status, created_date FROM crm_lead")
rows = cur.fetchall()
print(f"Total leads: {len(rows)}")
for r in rows:
    print(r)
