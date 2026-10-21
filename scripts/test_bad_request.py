import requests

base_url = "https://erpuma.pythonanywhere.com/api/drawings-2d/"

test_cases = [
    ("Empty body", {}),
    ("Null fields", {"title": None, "drawing_number": None, "design_job_id": None}),
    ("Category unknown", {"category": "RandomCategory", "drawing_number": "DWG-CAT-1"}),
    ("Status draft", {"status": "draft", "drawing_number": "DWG-DRAFT-1"}),
    ("Missing drawing_number", {"title": "No Drw Num"}),
    ("Null file_url", {"file_url": None, "drawing_number": "DWG-NULL-URL"}),
    ("Null designer", {"designer": None, "drawing_number": "DWG-NULL-DES"}),
    ("Extra fields from frontend", {
        "id": "DWG-2D-99111",
        "drawingNumber": "DWG-2D-99111",
        "drawingTitle": "Test",
        "partOrAssembly": "Assembly",
        "sheetSize": "A1",
        "scale": "1:10",
        "fileFormat": "PDF",
        "fileSize": "100 KB",
        "fileUrl": "",
        "drawingCategory": "GA",
        "status": "draft",
        "projectId": "",
        "jobNumber": "",
        "designJobId": "DES-01",
        "machineName": "Machine 1",
        "revision": "REV-01",
        "designer": "Admin",
        "uploadedDate": "2026-10-21"
    })
]

for name, payload in test_cases:
    r = requests.post(base_url, json=payload)
    print(f"[{name}] -> Status: {r.status_code}")
    if r.status_code != 201:
        print(f"   Response: {r.text}")
