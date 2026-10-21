import requests
import re

r = requests.get("https://erpuma.pythonanywhere.com/api/quotations/QT-2026-0143/pdf/", timeout=20)
m = re.search(r'<div id="summary">[\s\S]*?</div>', r.text)
if m:
    print(m.group(0))
else:
    m2 = re.search(r'<pre class="exception_value">([\s\S]*?)</pre>', r.text)
    if m2:
        print("Exception:", m2.group(1))
    else:
        print(r.text[:500])
