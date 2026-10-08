#!/usr/bin/env python3
"""
UmaERP - PythonAnywhere Deployment Runner Script
Executes atomic, safe deployment synchronization:
1. Git fetch & pull origin main (or checkout target rollback commit)
2. Dependency check & pip install if requirements.txt changed
3. Safe Django migrations (preserving existing production database)
4. Collectstatic
5. Touch WSGI file to trigger webapp reload
6. Append deployment log record
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON_BIN = sys.executable

# On PythonAnywhere, use virtualenv if detected
PA_VENV = Path('/home/erpUMA/.virtualenvs/erp-venv/bin')
if (PA_VENV / 'python').exists():
    PYTHON_BIN = str(PA_VENV / 'python')

PIP_BIN = str(Path(PYTHON_BIN).parent / 'pip')
WSGI_PATH = Path('/var/www/erpuma_pythonanywhere_com_wsgi.py')


def run_command(cmd, step_name, cwd=str(BASE_DIR), timeout=300):
    print(f"\n>>> [{step_name}] Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if res.stdout:
            print(res.stdout.strip())
        if res.stderr:
            print(f"STDERR: {res.stderr.strip()}", file=sys.stderr)
        return res.returncode == 0, res.stdout, res.stderr
    except Exception as e:
        print(f"EXCEPTION in [{step_name}]: {e}", file=sys.stderr)
        return False, "", str(e)


def get_commit_sha(rev="HEAD"):
    ok, out, _ = run_command(['git', 'rev-parse', rev], f"Get {rev} SHA")
    return out.strip() if ok else "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description="UmaERP Backend Deployment Runner")
    parser.add_argument('--rollback', help="Target commit SHA to roll back to", default=None)
    parser.add_argument('--force-pip', action='store_true', help="Force re-running pip install")
    parser.add_argument('--force-static', action='store_true', help="Force collectstatic")
    args = parser.parse_args()

    print("=" * 70)
    print("UMA ERP BACKEND - DEPLOYMENT SYNCHRONIZATION RUNNER")
    print("Timestamp:", datetime.now(timezone.utc).isoformat())
    print("Base Directory:", BASE_DIR)
    print("Python Executable:", PYTHON_BIN)
    print("=" * 70)

    previous_commit = get_commit_sha("HEAD")
    print(f"Current Working Commit (Before Deploy): {previous_commit}")

    # 1. Fetch remote origin
    ok_fetch, _, err_fetch = run_command(['git', 'fetch', 'origin', 'main'], "Git Fetch Origin Main")
    if not ok_fetch:
        print(f"ERROR: Could not fetch from origin: {err_fetch}")

    # 2. Check if requirements.txt changed
    reqs_changed = args.force_pip
    ok_diff, diff_out, _ = run_command(['git', 'diff', '--name-only', 'HEAD', 'origin/main'], "Diff Check")
    if ok_diff and 'requirements.txt' in diff_out:
        print("[NOTICE] requirements.txt has changed. Dependencies will be installed.")
        reqs_changed = True

    # 3. Checkout / Pull
    if args.rollback:
        print(f"\n[ROLLBACK MODE] Checking out target commit: {args.rollback}")
        ok_co, _, err_co = run_command(['git', 'checkout', args.rollback], f"Checkout {args.rollback}")
        if not ok_co:
            print(f"ERROR: Rollback failed: {err_co}")
            sys.exit(1)
    else:
        print("\n[DEPLOY MODE] Updating code to origin/main...")
        run_command(['git', 'checkout', 'main'], "Checkout Main")
        ok_pull, _, err_pull = run_command(['git', 'pull', 'origin', 'main'], "Git Pull Origin Main")
        if not ok_pull:
            print(f"WARNING: Git pull reported issues: {err_pull}")

    new_commit = get_commit_sha("HEAD")
    print(f"\nNew Working Commit (After Deploy): {new_commit}")

    # 4. Dependency Synchronization
    pip_status = "SKIPPED (No changes)"
    if reqs_changed:
        if Path(PIP_BIN).exists():
            ok_pip, _, _ = run_command([PIP_BIN, 'install', '-r', str(BASE_DIR / 'requirements.txt')], "Pip Install")
            pip_status = "PASS" if ok_pip else "FAILED"
        else:
            pip_status = "SKIPPED (pip not found)"
    else:
        pip_status = "PASS (Unchanged)"

    # 5. Database & Migration Safety
    ok_migrate, _, _ = run_command([PYTHON_BIN, 'manage.py', 'migrate', '--noinput'], "Django Migrations")
    migration_status = "PASS" if ok_migrate else "FAILED"

    # 6. Static files
    ok_static, _, _ = run_command([PYTHON_BIN, 'manage.py', 'collectstatic', '--noinput'], "Collect Static")
    static_status = "PASS" if ok_static else "FAILED"

    # 7. Reload WebApp via WSGI touch
    reload_status = "NOT_APPLICABLE (Non-PA)"
    if WSGI_PATH.exists():
        try:
            WSGI_PATH.touch()
            reload_status = "PASS (WSGI touched)"
            print("\n[RELOAD] Touched WSGI file:", WSGI_PATH)
        except Exception as e:
            reload_status = f"FAILED: {e}"

    # 8. Log deployment
    history_file = BASE_DIR / 'deployment_history.json'
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS" if (migration_status == "PASS" and ok_pull) else "WARNING",
        "previous_commit": previous_commit,
        "new_commit": new_commit,
        "branch": "main",
        "is_rollback": bool(args.rollback),
        "dependencies": pip_status,
        "migration": migration_status,
        "static": static_status,
        "reload": reload_status,
    }

    try:
        history = []
        if history_file.exists():
            try:
                history = json.loads(history_file.read_text())
            except Exception:
                history = []
        history.insert(0, record)
        history_file.write_text(json.dumps(history[:50], indent=2))
    except Exception as e:
        print("Could not update deployment history log:", e)

    print("\n" + "=" * 70)
    print("DEPLOYMENT RUNNER SUMMARY:")
    print("Previous Commit:    ", previous_commit)
    print("New Commit:         ", new_commit)
    print("Dependency Status:  ", pip_status)
    print("Migration Status:   ", migration_status)
    print("Static Files Status:", static_status)
    print("Webapp Reload:      ", reload_status)
    print("Overall Status:     ", "SUCCESS" if record["status"] == "SUCCESS" else "WARNING")
    print("=" * 70)

    if migration_status != "PASS":
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
