@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo    UMA ERP - BACKEND GIT PUSH & PYTHONANYWHERE DEPLOY
echo ========================================================

set /p MSG="Enter commit message (or press Enter for default): "
if "%MSG%"=="" (
    set MSG=update backend and sync to pythonanywhere
)

echo.
echo [1/3] Adding and committing changes to Git...
git add .
git commit -m "%MSG%"

echo.
echo [2/3] Pushing code to GitHub (https://github.com/infinitesofttech/BE-ERP-UMA)...
git push origin main

echo.
echo [3/3] Deploying code to PythonAnywhere (umaERP.pythonanywhere.com)...
python deploy_pythonanywhere.py

echo.
echo ========================================================
echo   SYNC COMPLETE! GitHub and PythonAnywhere are Updated!
echo ========================================================
pause
