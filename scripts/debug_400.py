import requests

base_url = "https://erpuma.pythonanywhere.com/api/drawings-2d/"

# Let's test with the EXACT payload structure from jobs/page.tsx handleSaveUploadDesign
# Look at jobs/page.tsx:
# drwNum = `DWG-${uploadingJob.jobNumber || uploadingJob.projectNumber || '2026'}-${Date.now().toString().slice(-3)}`
# drwTitle = modalDrawingTitle || ...
# drwRev = modalDrawingRevision || 'REV-01'
# drwCategory = modalDrawingCategory || 'GA'
# primaryFile = { name: 'IMG_20261021_150400.jpg', sizeText: '1.2 MB', type: 'image/jpeg', dataUrl: 'data:image/jpeg;base64,...' }
# addDrawing2D called:
# {
#   drawingNumber: drwNum,
#   projectId: 'PRJ-2026-0009',
#   jobNumber: 'JOB-2026-0009',
#   designJobId: 'DES-PRJ-2026-0009-1',
#   machineName: 'mahadev workers folloers',
#   drawingTitle: '3D Modeling, General Arrangement (GA) Drawing & Fabrication Detailing',
#   category: 'GA',
#   revision: 'REV-01',
#   designer: 'Super Admin Hardik',
#   fileFormat: 'JPG',
#   fileUrl: 'data:image/jpeg;base64,' + 'B' * 1000,
#   fileSize: '1.2 MB',
#   status: 'draft',
# }

# In ERPContext.tsx:
# const id = `DWG-2D-${Date.now().toString().slice(-5)}`;
# payload = {
#   ...newDrw,
#   design_job_id: newDrw.designJobId || ...,
#   drawing_number: newDrw.drawingNumber || ...,
#   title: newDrw.drawingTitle || ...,
#   revision: newDrw.revision || ...,
#   prepared_by: newDrw.designer || ...,
#   sheet_size: newDrw.sheetSize || 'A1',
#   file_url: newDrw.fileUrl || '',
# }

payload = {
    "drawingNumber": "DWG-JOB-2026-0009-999",
    "projectId": "PRJ-2026-0009",
    "jobNumber": "JOB-2026-0009",
    "designJobId": "DES-PRJ-2026-0009-1",
    "machineName": "mahadev workers folloers",
    "drawingTitle": "3D Modeling, General Arrangement (GA) Drawing & Fabrication Detailing",
    "category": "GA",
    "revision": "REV-01",
    "designer": "Super Admin Hardik",
    "fileFormat": "JPG",
    "fileUrl": "data:image/jpeg;base64," + "B" * 5000,
    "fileSize": "1.2 MB",
    "status": "draft",
    "id": "DWG-2D-98765",
    "uploadedDate": "2026-10-21",
    "design_job_id": "DES-PRJ-2026-0009-1",
    "drawing_number": "DWG-JOB-2026-0009-999",
    "title": "3D Modeling, General Arrangement (GA) Drawing & Fabrication Detailing",
    "revision": "REV-01",
    "prepared_by": "Super Admin Hardik",
    "sheet_size": "A1",
    "file_url": "data:image/jpeg;base64," + "B" * 5000,
}

r = requests.post(base_url, json=payload)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
