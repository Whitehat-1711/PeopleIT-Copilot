# WorkPulse AI — PowerShell Helper Script
param (
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "ingest", "test", "api", "ui", "db", "help")]
    [string]$Command = "help"
)

$VENV_PY = Join-Path $PSScriptRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $VENV_PY)) {
    $VENV_PY = "python"
}

switch ($Command) {
    "up" {
        Write-Host "🚀 Starting Docker containers (Postgres & ChromaDB)..." -ForegroundColor Cyan
        docker compose up -d postgres chromadb
    }
    "down" {
        Write-Host "🛑 Stopping Docker containers..." -ForegroundColor Yellow
        docker compose down
    }
    "ingest" {
        Write-Host "📚 Ingesting policy documents into ChromaDB..." -ForegroundColor Cyan
        Set-Location (Join-Path $PSScriptRoot "backend")
        & $VENV_PY -m backend.ingest
    }
    "test" {
        Write-Host "🧪 Running test suite..." -ForegroundColor Cyan
        Set-Location (Join-Path $PSScriptRoot "backend")
        & $VENV_PY -m pytest tests/ -v
    }
    "api" {
        Write-Host "⚡ Starting FastAPI Backend on http://127.0.0.1:8001..." -ForegroundColor Green
        Set-Location (Join-Path $PSScriptRoot "backend")
        & $VENV_PY -m uvicorn backend.api:app --host 127.0.0.1 --port 8001 --reload
    }
    "ui" {
        Write-Host "💼 Starting WorkPulse AI Streamlit UI on http://localhost:8501..." -ForegroundColor Green
        & $VENV_PY -m streamlit run (Join-Path $PSScriptRoot "frontend\app.py") --server.port 8501 --server.address 127.0.0.1
    }
    "db" {
        Write-Host "🐘 Connecting to PostgreSQL (company_db)..." -ForegroundColor Cyan
        docker exec -it hr_it_postgres psql -U admin -d company_db
    }
    Default {
        Write-Host "WorkPulse AI - Management Commands:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 up      - Start Postgres & ChromaDB containers"
        Write-Host "  .\run.ps1 down    - Stop all containers"
        Write-Host "  .\run.ps1 ingest  - Embed and ingest policy documents"
        Write-Host "  .\run.ps1 test    - Run complete pytest test suite"
        Write-Host "  .\run.ps1 api     - Start FastAPI backend server (port 8001)"
        Write-Host "  .\run.ps1 ui      - Start Streamlit frontend (port 8501)"
        Write-Host "  .\run.ps1 db      - Open interactive PostgreSQL terminal"
    }
}
