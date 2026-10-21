import requests

base_url = "https://erpuma.pythonanywhere.com/api/drawings-2d/"

# 1. Test with small payload
p1 = {
    "drawingNumber": f"DWG-TEST-{int(10000)}",
    "title": "Small Test",
    "designJobId": "DJ-001",
    "file_url": "data:image/png;base64,abc"
}
r1 = requests.post(base_url, json=p1)
print(f"Test 1 (Small): {r1.status_code} - {r1.text[:200]}")

# 2. Test with medium base64 (500 KB)
dummy_500kb = "data:image/jpeg;base64," + ("A" * (500 * 1024))
p2 = {
    "drawingNumber": f"DWG-TEST-{int(10001)}",
    "title": "500KB Test",
    "designJobId": "DJ-001",
    "file_url": dummy_500kb
}
r2 = requests.post(base_url, json=p2)
print(f"Test 2 (500KB): {r2.status_code} - {r2.text[:200]}")

# 3. Test with large base64 (2.5 MB)
dummy_2_5mb = "data:image/jpeg;base64," + ("A" * (2600 * 1024))
p3 = {
    "drawingNumber": f"DWG-TEST-{int(10002)}",
    "title": "2.5MB Test",
    "designJobId": "DJ-001",
    "file_url": dummy_2_5mb
}
r3 = requests.post(base_url, json=p3)
print(f"Test 3 (2.5MB): {r3.status_code} - {r3.text[:200]}")

# 4. Test with exact fields sent by frontend when user clicked upload
p4 = {
    "drawingNumber": "DWG-2026-0009-888",
    "projectId": "PRJ-2026-0009",
    "jobNumber": "JOB-2026-0009",
    "designJobId": "DES-PRJ-2026-0009-1",
    "machineName": "mahadev workers folloers",
    "drawingTitle": "GA Drawing",
    "category": "GA",
    "revision": "REV-01",
    "designer": "Super Admin Hardik",
    "fileFormat": "IMAGE",
    "fileUrl": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
    "fileSize": "1.2 MB",
    "status": "draft",
    "id": "DWG-2D-99999",
    "uploadedDate": "2026-10-21",
    "design_job_id": "DES-PRJ-2026-0009-1",
    "drawing_number": "DWG-2026-0009-888",
    "title": "GA Drawing",
    "prepared_by": "Super Admin Hardik",
    "sheet_size": "A1",
    "file_url": "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
}
r4 = requests.post(base_url, json=p4)
print(f"Test 4 (Exact frontend payload): {r4.status_code} - {r4.text[:200]}")

# 5. What if drawingNumber already exists?
r5 = requests.post(base_url, json=p4)
print(f"Test 5 (Duplicate ID / drawingNumber): {r5.status_code} - {r5.text[:200]}")
