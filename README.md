# Zhandui Online

This repository tracks the source currently deployed at `zhanduiwang.top`.

## Verify

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Set-Location frontend
npm ci
Set-Location ..
.\scripts\test.ps1
```

Production secrets belong in `/etc/zhandui/zhandui.env` and must never be committed.
