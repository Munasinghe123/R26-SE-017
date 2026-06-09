param (
    [string]$target = "help"
)

switch ($target) {
    "orchestrator" {
        Set-Location services/orchestrator
        python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    }
    "agent1" {
        Set-Location services/agent1-requirements
        python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
    }
    "agent2" {
        Set-Location services/agent2-hld
        python -m uvicorn server:app --host 0.0.0.0 --port 8002 --reload
    }
    "agent3" {
        Set-Location services/agent3-lld
        python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload
    }
    "agent4" {
        Set-Location services/agent4-ui
        python -m uvicorn api:app --host 0.0.0.0 --port 8004 --reload
    }
    "srs" {
        Set-Location services/srs-assembler
        python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload
    }
    "web" {
        Set-Location apps/web
        npm run dev
    }
    "db" {
        python infra/create_tables.py
        python infra/create_users_table.py
        python infra/verify_tables.py
    }
    "all" {
        Write-Host "🚀 Launching full Multi-Agent System (Ports 8000-8005 + Web 5173)..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/services/orchestrator'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/services/agent1-requirements'; python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/services/agent2-hld'; python -m uvicorn server:app --host 0.0.0.0 --port 8002 --reload"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/services/agent3-lld'; python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/services/agent4-ui'; python -m uvicorn api:app --host 0.0.0.0 --port 8004 --reload"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/services/srs-assembler'; python -m uvicorn main:app --host 0.0.0.0 --port 8005 --reload"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/apps/web'; npm run dev"
        Write-Host "✅ All 7 system services launched!" -ForegroundColor Cyan
    }
    default {
        Write-Host "Usage: .\run.ps1 <target>" -ForegroundColor Cyan
        Write-Host "Available targets:"
        Write-Host "  all          - Launch ENTIRE system (Ports 8000-8005 + Web 5173)" -ForegroundColor Yellow
        Write-Host "  orchestrator - Start Orchestrator (port 8000)"
        Write-Host "  agent1       - Start Agent 1 Requirements (port 8001)"
        Write-Host "  agent2       - Start Agent 2 HLD (port 8002)"
        Write-Host "  agent3       - Start Agent 3 LLD (port 8003)"
        Write-Host "  agent4       - Start Agent 4 UI (port 8004)"
        Write-Host "  srs          - Start SRS Assembler (port 8005)"
        Write-Host "  web          - Start React Frontend (port 5173)"
        Write-Host "  db           - Run DB table setup and verification"
    }
}
