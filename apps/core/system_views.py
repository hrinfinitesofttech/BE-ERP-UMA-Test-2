import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


def get_current_git_commit():
    """
    Retrieves the current git commit SHA from .git directory or via git command.
    Works reliably both locally and inside PythonAnywhere.
    """
    base_dir = Path(settings.BASE_DIR)
    git_dir = base_dir / '.git'
    
    # 1. Try reading .git/refs/heads/main
    ref_main = git_dir / 'refs' / 'heads' / 'main'
    if ref_main.exists():
        try:
            return ref_main.read_text().strip()
        except Exception:
            pass

    # 2. Try reading .git/HEAD directly if detached or packed
    head_file = git_dir / 'HEAD'
    if head_file.exists():
        try:
            content = head_file.read_text().strip()
            if content.startswith('ref: '):
                ref_path = git_dir / content[5:].strip()
                if ref_path.exists():
                    return ref_path.read_text().strip()
            else:
                return content
        except Exception:
            pass

    # 3. Fallback to git command
    try:
        res = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass

    return "UNKNOWN"


def get_current_git_branch():
    """Returns current active branch name."""
    base_dir = Path(settings.BASE_DIR)
    try:
        head_file = base_dir / '.git' / 'HEAD'
        if head_file.exists():
            content = head_file.read_text().strip()
            if content.startswith('ref: refs/heads/'):
                return content.replace('ref: refs/heads/', '').strip()
    except Exception:
        pass
    return "main"


class SystemHealthView(View):
    """
    Health check endpoint for UMA ERP Backend.
    Reports API readiness, live git commit, database status, and runtime environment.
    """
    def get(self, request, *args, **kwargs):
        # 1. Database check
        db_status = "CONNECTED"
        db_error = None
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            db_status = "ERROR"
            db_error = str(e)

        commit = get_current_git_commit()
        branch = get_current_git_branch()
        is_pa = 'PYTHONANYWHERE_DOMAIN' in os.environ or 'erpUMA' in str(settings.BASE_DIR)

        payload = {
            "status": "HEALTHY" if db_status == "CONNECTED" else "DEGRADED",
            "service": "UmaERP Backend API",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "git_commit": commit,
            "git_short_commit": commit[:7] if commit != "UNKNOWN" else "UNKNOWN",
            "branch": branch,
            "database": db_status,
            "database_engine": settings.DATABASES['default']['ENGINE'].split('.')[-1],
            "python_version": sys.version.split()[0],
            "django_version": getattr(settings, 'DJANGO_VERSION', '4.2'),
            "environment": "pythonanywhere_production" if is_pa else "development",
            "sync_engine_version": "2.0-automated-sync",
            "deployment_pipeline": "github-actions-pa-sync-active",
        }
        if db_error:
            payload["database_error"] = db_error

        http_status = 200 if db_status == "CONNECTED" else 503
        return JsonResponse(payload, status=http_status)


@method_decorator(csrf_exempt, name='dispatch')
class SystemDeployView(View):
    """
    Secure webhook endpoint for automated backend deployment and synchronization.
    Accepts POST requests authenticated via X-Deploy-Token or Authorization Bearer.
    Pulls code from GitHub, applies migrations safely, updates static files, touches WSGI, and logs result.
    """
    def post(self, request, *args, **kwargs):
        # 1. Security Authorization Check
        expected_token = getattr(settings, 'DEPLOY_SECRET_KEY', 'uma-erp-deploy-key-2026-secure-sync')
        received_token = (
            request.headers.get('X-Deploy-Token')
            or request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        )

        if not received_token or received_token != expected_token:
            return JsonResponse({
                "status": "FORBIDDEN",
                "error": "Invalid or missing deployment authorization token."
            }, status=403)

        # 2. Parse request payload if any
        target_commit = None
        force_pip = False
        try:
            if request.body:
                body_data = json.loads(request.body.decode('utf-8'))
                target_commit = body_data.get('target_commit')
                force_pip = body_data.get('force_pip', False)
        except Exception:
            pass

        base_dir = str(settings.BASE_DIR)
        python_bin = sys.executable

        # Detect virtualenv python if available
        pa_venv_python = Path('/home/erpUMA/.virtualenvs/erp-venv/bin/python')
        if pa_venv_python.exists():
            python_bin = str(pa_venv_python)

        pip_bin = str(Path(python_bin).parent / 'pip')

        previous_commit = get_current_git_commit()
        logs = []
        errors = []

        def run_step(cmd_list, step_name):
            try:
                res = subprocess.run(
                    cmd_list,
                    cwd=base_dir,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                output = f"[{step_name}]\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}\nEXIT:{res.returncode}"
                logs.append(output)
                if res.returncode != 0:
                    errors.append(f"{step_name} failed with code {res.returncode}: {res.stderr}")
                    return False, res.stdout, res.stderr
                return True, res.stdout, res.stderr
            except Exception as e:
                err = f"{step_name} exception: {str(e)}"
                logs.append(err)
                errors.append(err)
                return False, "", str(e)

        # Step 1: Git fetch origin main
        run_step(['git', 'fetch', 'origin', 'main'], "Git Fetch")

        # Step 2: Check diff to see if requirements.txt changed
        reqs_changed = force_pip
        diff_ok, diff_out, _ = run_step(['git', 'diff', '--name-only', 'HEAD', 'origin/main'], "Git Diff")
        if 'requirements.txt' in diff_out:
            reqs_changed = True

        # Step 3: Git checkout / pull
        if target_commit:
            run_step(['git', 'checkout', target_commit], f"Git Checkout {target_commit}")
        else:
            run_step(['git', 'checkout', 'main'], "Git Checkout Main")
            run_step(['git', 'pull', 'origin', 'main'], "Git Pull")

        new_commit = get_current_git_commit()

        # Step 4: Pip install if requirements changed
        if reqs_changed and Path(pip_bin).exists():
            run_step([pip_bin, 'install', '-r', 'requirements.txt'], "Pip Install")

        # Step 5: Safe Django Migrations (Never drops database)
        run_step([python_bin, 'manage.py', 'migrate', '--noinput'], "Django Migrate")

        # Step 6: Collect static files
        run_step([python_bin, 'manage.py', 'collectstatic', '--noinput'], "Collect Static")

        # Step 7: Touch WSGI file to trigger PythonAnywhere web worker reload
        wsgi_touched = False
        wsgi_path = Path('/var/www/erpuma_pythonanywhere_com_wsgi.py')
        if wsgi_path.exists():
            try:
                wsgi_path.touch()
                wsgi_touched = True
                logs.append("[WSGI Touch] Successfully touched WSGI file for reload.")
            except Exception as e:
                logs.append(f"[WSGI Touch] Could not touch WSGI: {e}")

        # Step 8: Record Deployment History Log
        history_file = Path(base_dir) / 'deployment_history.json'
        deploy_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SUCCESS" if not errors else "WARNING_OR_ERROR",
            "previous_commit": previous_commit,
            "new_commit": new_commit,
            "target_commit": target_commit or "HEAD",
            "requirements_updated": reqs_changed,
            "wsgi_touched": wsgi_touched,
            "errors": errors,
        }

        try:
            history = []
            if history_file.exists():
                try:
                    history = json.loads(history_file.read_text())
                except Exception:
                    history = []
            history.insert(0, deploy_record)
            history_file.write_text(json.dumps(history[:50], indent=2))
        except Exception:
            pass

        response_status = 200 if not errors else 207  # 207 Multi-Status if warnings
        return JsonResponse({
            "status": "SUCCESS" if not errors else "COMPLETED_WITH_WARNINGS",
            "timestamp": deploy_record["timestamp"],
            "previous_commit": previous_commit,
            "new_commit": new_commit,
            "synchronized": (previous_commit != new_commit) or (target_commit is not None),
            "requirements_updated": reqs_changed,
            "wsgi_touched": wsgi_touched,
            "errors": errors,
            "logs": logs,
        }, status=response_status)
