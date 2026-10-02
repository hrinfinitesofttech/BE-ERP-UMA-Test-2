import requests

BASE_URL = 'https://umaERP.pythonanywhere.com/api'

def run_tests():
    print('=====================================================')
    print('   FULL VERIFICATION: DESIGN JOB RELEASE & DB SAVE   ')
    print('=====================================================')
    
    # Step 1: Initial list
    print('\n[1/3] Fetching current jobs from PythonAnywhere DB...')
    r1 = requests.get(f'{BASE_URL}/designer/jobs/')
    print('Status Code:', r1.status_code)
    initial_jobs = r1.json() if r1.status_code == 200 else []
    print(f'Total jobs retrieved: {len(initial_jobs)}')
    for j in initial_jobs:
        print(f"  * {j.get('id')} | Status: {j.get('status')} | Customer: {j.get('customerName')} | Remarks: {j.get('remarks')}")

    # Step 2: Release a pending job (e.g. DES-2026-0008)
    print('\n[2/3] Simulating user clicking \"Release Now\" for DES-2026-0008...')
    release_payload = {
        'id': 'DES-2026-0008',
        'designJobNumber': 'DES-2026-0008',
        'jobNumber': 'JOB-2026-0051',
        'projectId': 'PRJ-2026-0041',
        'customerName': 'Ravi Aluminium PVT LTD',
        'productName': 'Custom Equipment (Ref QT-2026-0133 (Rev-00))',
        'assignedDesigner': 'Dharmesh Joshi',
        'designManager': 'Ketan Patel',
        'releasedBy': 'Admin User',
        'remarks': 'Released to shop floor by Admin User on 10/1/2026'
    }
    r2 = requests.post(f'{BASE_URL}/designer/jobs/DES-2026-0008/release-to-production/', json=release_payload)
    print('Release POST Status:', r2.status_code)
    if r2.status_code == 200:
        res_data = r2.json()
        print('Success Message:', res_data.get('message'))
        print('Saved Job in DB:', res_data.get('job', {}).get('id'), '| Status:', res_data.get('job', {}).get('status'))
    else:
        print('Error Response:', r2.text[:300])

    # Step 3: Re-fetch (simulating user refreshing browser page / F5)
    print('\n[3/3] Simulating Page Refresh (F5) - Re-fetching from Database...')
    r3 = requests.get(f'{BASE_URL}/designer/jobs/')
    print('Re-fetch Status:', r3.status_code)
    updated_jobs = r3.json() if r3.status_code == 200 else []
    
    target = next((j for j in updated_jobs if j.get('id') == 'DES-2026-0008'), None)
    if target and target.get('status') == 'released_to_production':
        print('\n>>> [PASS] PERSISTENCE VERIFIED! <<<')
        print(f"Job: {target.get('id')}")
        print(f"Status in DB: {target.get('status')}")
        print(f"Remarks in DB: {target.get('remarks')}")
        print(f"Approved By: {target.get('approvedBy')}")
    else:
        print('\n>>> [FAIL] Job status was not saved as released in DB! <<<')
        print('Actual target:', target)

    print('\n=====================================================')

if __name__ == '__main__':
    run_tests()
