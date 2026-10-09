#!/usr/bin/env python3
"""
UmaERP - GitHub to PythonAnywhere Automatic Deployment & Synchronization Engine
Features:
- Single Source of Truth: Enforces GitHub origin/main == PythonAnywhere HEAD
- Two-Tier Deployment:
    Tier 1: High-speed authenticated API Webhook (/api/system/deploy/)
    Tier 2: Out-of-band PythonAnywhere REST API Bootstrapper & WSGI reloader
- Dependency & Migration Safety: Detects requirements.txt changes, runs migrations without data loss
- Code Drift Prevention: Verifies GitHub SHA == PythonAnywhere Deployed SHA
- Health Checks: Verifies live API endpoints after reload
- Rollback Capability: Supports one-command instant rollback
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime, timezone
from pathlib import Path

# Configuration defaults (can be overridden via environment variables)
PA_USERNAME = os.environ.get('PA_USERNAME', 'erpUMA')
PA_API_TOKEN = os.environ.get('PA_API_TOKEN', 'e023a655a10e258afcd2b8ff184bdc339fd4c30a')
PA_DOMAIN = os.environ.get('PA_DOMAIN', 'erpuma.pythonanywhere.com')
DEPLOY_SECRET = os.environ.get('DEPLOY_SECRET_KEY', 'uma-erp-deploy-key-2026-secure-sync')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'hrinfinitesofttech/BE-ERP-UMA-Test-2')
BRANCH = os.environ.get('DEPLOY_BRANCH', 'main')

PA_BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{PA_USERNAME}"
LIVE_BASE_URL = f"https://{PA_DOMAIN}"

PA_HEADERS = {
    'Authorization': f'Token {PA_API_TOKEN}',
    'User-Agent': 'UmaERP-Deployment-Engine/1.0',
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def get_github_latest_commit():
    """Fetches the latest commit SHA from GitHub API for the target branch."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{BRANCH}"
    try:
        r = requests.get(url, headers={'User-Agent': 'UmaERP-Deployer'}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get('sha'), data.get('commit', {}).get('message', '').strip().split('\n')[0]
        else:
            log(f"GitHub API notice (HTTP {r.status_code}): {r.text[:100]}")
    except Exception as e:
        log(f"GitHub API connection warning: {e}")
    return None, None


def get_pa_deployed_commit_via_file():
    """Reads the exact deployed git commit from PythonAnywhere via Files API."""
    url_head = f"{PA_BASE_URL}/files/path/home/{PA_USERNAME}/BE-ERP-UMA/.git/HEAD"
    try:
        r = requests.get(url_head, headers=PA_HEADERS, timeout=15)
        if r.status_code == 200:
            head_val = r.text.strip()
            if head_val.startswith("ref: "):
                ref_rel = head_val.replace("ref: ", "").strip()
                r_ref = requests.get(f"{PA_BASE_URL}/files/path/home/{PA_USERNAME}/BE-ERP-UMA/.git/{ref_rel}", headers=PA_HEADERS, timeout=15)
                if r_ref.status_code == 200:
                    return r_ref.text.strip()
            else:
                return head_val
    except Exception as e:
        log(f"Error fetching HEAD via Files API: {e}")

    url_main = f"{PA_BASE_URL}/files/path/home/{PA_USERNAME}/BE-ERP-UMA/.git/refs/heads/{BRANCH}"
    try:
        r = requests.get(url_main, headers=PA_HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text.strip()
    except Exception as e:
        log(f"Error fetching PA commit via Files API: {e}")
    return "UNKNOWN"


def reload_pa_webapp():
    """Reloads the PythonAnywhere web application via REST API."""
    url = f"{PA_BASE_URL}/webapps/{PA_DOMAIN}/reload/"
    try:
        r = requests.post(url, headers=PA_HEADERS, timeout=30)
        return r.status_code == 200, r.status_code, r.text
    except Exception as e:
        return False, 500, str(e)


def deploy_via_webhook(target_commit=None, force_pip=False):
    """Tier 1: Triggers deployment via the live Django webhook."""
    url = f"{LIVE_BASE_URL}/api/system/deploy/"
    headers = {
        'X-Deploy-Token': DEPLOY_SECRET,
        'Content-Type': 'application/json',
    }
    payload = {
        'target_commit': target_commit,
        'force_pip': force_pip,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code in [200, 207]:
            return True, r.json()
        return False, {"status_code": r.status_code, "text": r.text[:200]}
    except Exception as e:
        return False, {"error": str(e)}


def deploy_via_pa_bootstrap(target_commit=None):
    """
    Tier 2 Fallback: If webhook is unavailable (e.g., initial setup or syntax error),
    uses PythonAnywhere WSGI hook to run git pull/checkout and migrations safely.
    """
    log("Tier 1 Webhook not reachable. Engaging Tier 2 PA Bootstrap Engine...")
    cmd_git = f"git checkout {target_commit}" if target_commit else "git checkout main && git pull origin main"
    
    bootstrap_wsgi = f"""import os
import sys
import subprocess

path = '/home/{PA_USERNAME}/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

# Execute atomic deployment bootstrap
try:
    p_git = subprocess.run('{cmd_git}', shell=True, cwd=path, capture_output=True, text=True, timeout=60)
    p_mig = subprocess.run('/home/{PA_USERNAME}/.virtualenvs/erp-venv/bin/python manage.py migrate --noinput', shell=True, cwd=path, capture_output=True, text=True, timeout=90)
    with open('/home/{PA_USERNAME}/deploy_bootstrap_status.txt', 'w') as f:
        f.write(f"GIT_CODE:{{p_git.returncode}}\\nGIT_OUT:{{p_git.stdout}}\\nGIT_ERR:{{p_git.stderr}}\\nMIG_CODE:{{p_mig.returncode}}\\nMIG_OUT:{{p_mig.stdout}}\\n")
except Exception as e:
    with open('/home/{PA_USERNAME}/deploy_bootstrap_status.txt', 'w') as f:
        f.write(f"BOOTSTRAP_EXCEPTION: {{e}}")

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""
    clean_wsgi = f"""import os
import sys

path = '/home/{PA_USERNAME}/BE-ERP-UMA'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'erp_backend.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""
    wsgi_url = f"{PA_BASE_URL}/files/path/var/www/erpuma_pythonanywhere_com_wsgi.py"
    
    # 1. Inject bootstrap WSGI
    r_up = requests.post(wsgi_url, headers=PA_HEADERS, files={'content': bootstrap_wsgi})
    if r_up.status_code != 200:
        return False, "Failed to upload bootstrap WSGI"
        
    # 2. Reload to trigger bootstrap
    reload_pa_webapp()
    time.sleep(3)
    try:
        requests.get(f"{LIVE_BASE_URL}/api/", timeout=15)
    except Exception:
        pass
        
    # 3. Restore clean WSGI
    requests.post(wsgi_url, headers=PA_HEADERS, files={'content': clean_wsgi})
    reload_pa_webapp()
    time.sleep(2)
    return True, "Bootstrap deployment executed successfully"


def verify_live_api():
    """Tests critical live API endpoints and checks health."""
    results = {}
    endpoints = [
        ('/api/system/health/', 'System Health'),
        ('/api/', 'Root API Router'),
        ('/api/projects/', 'Projects Master'),
        ('/api/sales-orders/', 'Sales Orders'),
        ('/api/crm/leads/', 'CRM Leads'),
    ]
    for path, name in endpoints:
        url = f"{LIVE_BASE_URL}{path}"
        try:
            r = requests.get(url, timeout=12)
            results[name] = {
                "status_code": r.status_code,
                "ok": r.status_code in [200, 401],  # 401 means auth protected (service healthy)
                "body": r.json() if (r.status_code == 200 and 'json' in r.headers.get('Content-Type', '')) else None
            }
        except Exception as e:
            results[name] = {"status_code": 0, "ok": False, "error": str(e)}
    return results


def check_status_only():
    """Queries and displays synchronization status between GitHub and PythonAnywhere."""
    gh_sha, gh_msg = get_github_latest_commit()
    pa_sha = get_pa_deployed_commit_via_file()
    api_check = verify_live_api()
    health_data = api_check.get('System Health', {}).get('body', {})
    live_sha = health_data.get('git_commit', 'UNKNOWN') if health_data else 'UNKNOWN'

    synced = (gh_sha and pa_sha and gh_sha == pa_sha)

    print("=" * 70)
    print("UMA ERP BACKEND - SYNCHRONIZATION STATUS AUDIT")
    print("=" * 70)
    print(f"Target Repository:    https://github.com/{GITHUB_REPO}")
    print(f"Branch:               {BRANCH}")
    print(f"GitHub Latest Commit: {gh_sha} ({gh_msg or 'N/A'})")
    print(f"PythonAnywhere HEAD:  {pa_sha}")
    print(f"Live API Commit:      {live_sha}")
    print(f"Code Sync Status:     {'SYNCHRONIZED' if synced else 'NOT SYNCHRONIZED (DRIFT DETECTED)'}")
    print(f"Live API Health:      {'ONLINE' if api_check.get('Root API Router', {}).get('ok') else 'OFFLINE'}")
    print("=" * 70)
    return synced


def main():
    parser = argparse.ArgumentParser(description="UmaERP Backend GitHub to PythonAnywhere Deployer")
    parser.add_argument('--status', action='store_true', help="Check sync status without deploying")
    parser.add_argument('--rollback', help="Commit SHA to roll back to", default=None)
    parser.add_argument('--force-pip', action='store_true', help="Force re-installing requirements.txt")
    parser.add_argument('--ci', action='store_true', help="Run in CI/CD non-interactive mode")
    args = parser.parse_args()

    if args.status:
        is_synced = check_status_only()
        sys.exit(0 if is_synced else 1)

    start_time = datetime.now(timezone.utc)
    print("=" * 75)
    print("UMA ERP BACKEND - AUTOMATIC DEPLOYMENT & SYNCHRONIZATION ENGINE")
    print(f"Execution Mode: {'ROLLBACK' if args.rollback else 'AUTOMATIC DEPLOY'}")
    print(f"Timestamp:      {start_time.isoformat()}")
    print(f"Target Branch:  {BRANCH}")
    print("=" * 75)

    # 1. Fetch GitHub Target Commit
    gh_sha, gh_msg = get_github_latest_commit()
    target_sha = args.rollback if args.rollback else gh_sha
    log(f"GitHub Remote HEAD Commit: {gh_sha} ({gh_msg or 'Latest'})")
    if args.rollback:
        log(f"Rollback Target Commit:    {args.rollback}")

    # 2. Check PythonAnywhere Current Commit
    prev_pa_sha = get_pa_deployed_commit_via_file()
    log(f"PythonAnywhere Current SHA: {prev_pa_sha}")

    # 3. Trigger Deployment
    log("Deploying latest changes to PythonAnywhere...")
    deploy_ok, deploy_info = deploy_via_webhook(target_commit=target_sha, force_pip=args.force_pip)
    
    if not deploy_ok:
        log(f"Webhook deploy encountered issue: {deploy_info}. Falling back to Tier 2 Bootstrap...")
        deploy_ok, deploy_info = deploy_via_pa_bootstrap(target_commit=target_sha)

    # 4. Trigger WebApp Reload
    log("Reloading PythonAnywhere Web Application...")
    reload_ok, reload_code, _ = reload_pa_webapp()
    log(f"WebApp Reload Status: HTTP {reload_code} ({'PASS' if reload_ok else 'WARN'})")

    # 5. Allow worker startup
    time.sleep(4)

    # 6. Verify Deployed Commit
    new_pa_sha = get_pa_deployed_commit_via_file()
    log(f"PythonAnywhere Deployed Commit: {new_pa_sha}")

    # 7. Verify Live API & Health Check
    log("Verifying Live API Health Endpoints...")
    api_results = verify_live_api()
    health_body = api_results.get('System Health', {}).get('body') or {}
    live_api_sha = health_body.get('git_commit', new_pa_sha)

    # 8. Check Commit Parity
    target_for_check = args.rollback if args.rollback else gh_sha
    is_synchronized = False
    if target_for_check and new_pa_sha:
        is_synchronized = new_pa_sha.startswith(target_for_check) or target_for_check.startswith(new_pa_sha)

    all_apis_ok = all(v.get('ok', False) for v in api_results.values())
    overall_status = "SUCCESS" if (is_synchronized and all_apis_ok) else "FAILED"

    # 9. Format Deployment Record (Matches Section 10 & 11)
    print("\n" + "=" * 75)
    print("DEPLOYMENT VERIFICATION RECORD")
    print("=" * 75)
    print(f"Deployment Date/Time:   {start_time.isoformat()}")
    print(f"GitHub Repository:      https://github.com/{GITHUB_REPO}")
    print(f"Branch:                 {BRANCH}")
    print(f"Previous Commit:        {prev_pa_sha}")
    print(f"Target Commit:          {target_for_check}")
    print(f"PythonAnywhere Commit:  {new_pa_sha}")
    print(f"Live API Commit:        {live_api_sha}")
    print("---------------------------------------------------------------------------")
    print(f"Git Synchronization:    {'PASS (SYNCHRONIZED)' if is_synchronized else 'FAIL (NOT SYNCHRONIZED)'}")
    print(f"Django Startup / Health:{'PASS' if api_results.get('System Health', {}).get('ok') else 'FAIL'}")
    print(f"Root API Status:        {'PASS' if api_results.get('Root API Router', {}).get('ok') else 'FAIL'}")
    print(f"Business APIs Check:    {'PASS' if all_apis_ok else 'FAIL'}")
    print(f"Web Reload Status:      {'PASS' if reload_ok else 'FAIL'}")
    print(f"FINAL DEPLOYMENT STATUS:{overall_status}")
    print("=" * 75)

    for ep_name, ep_data in api_results.items():
        status_str = f"HTTP {ep_data.get('status_code')}" if ep_data.get('status_code') else f"ERROR: {ep_data.get('error')}"
        print(f"  • {ep_name.ljust(22)}: {status_str}")
    print("=" * 75 + "\n")

    if overall_status == "SUCCESS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
