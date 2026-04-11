Set-Location "P:\SkillIQ"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
Write-Host ""
Write-Host "SkillIQ Server Starting"
Write-Host "Frontend:  http://127.0.0.1:8000/"
Write-Host "Auth Page: http://127.0.0.1:8000/auth.html"
Write-Host "API Docs:  http://127.0.0.1:8000/docs"
Write-Host ""
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
