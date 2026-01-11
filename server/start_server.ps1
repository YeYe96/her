# ================================================================
# Amadeus 后端服务启动脚本
# ================================================================
# 简约版：直接启动，不含复杂的自动重试逻辑
# ================================================================

$ServerPort = 8020

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Amadeus Server (Simple Launcher)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 简单检查一下端口，如果占用就尝试杀一次，不行就报错
$netstat = netstat -ano | Select-String ":$ServerPort\s.*LISTENING"
if ($netstat) {
    Write-Host "Port $ServerPort is busy. Trying to clear..." -ForegroundColor Yellow
    $procId = ($netstat -split '\s+')[-1]
    taskkill /F /PID $procId 2>$null | Out-Null
    Start-Sleep -Seconds 1
}

# 2. 设置环境变量
$env:OLLAMA_HOST = "http://localhost:11434"

# 3. 启动服务
Write-Host "Starting Uvicorn on port $ServerPort..." -ForegroundColor Green
Write-Host "OLLAMA_HOST: $env:OLLAMA_HOST" -ForegroundColor Gray
Write-Host ""

Set-Location -Path $PSScriptRoot
python -m uvicorn main:app --host 0.0.0.0 --port $ServerPort

