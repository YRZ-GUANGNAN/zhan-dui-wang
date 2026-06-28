$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Missing .venv. Run: python -m venv .venv'
}
Push-Location $root
try {
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }

    Push-Location (Join-Path $root 'frontend')
    try {
        npm audit --omit=dev
        if ($LASTEXITCODE -ne 0) { throw 'Frontend audit failed' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}
