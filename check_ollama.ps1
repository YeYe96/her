# Ollama 配置检查脚本
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Ollama 配置检查" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查环境变量
Write-Host "1. 检查环境变量 OLLAMA_HOST:" -ForegroundColor Yellow
$ollamaHost = [System.Environment]::GetEnvironmentVariable('OLLAMA_HOST', 'User')
if ($ollamaHost) {
    Write-Host "   ✓ OLLAMA_HOST = $ollamaHost" -ForegroundColor Green
} else {
    Write-Host "   ✗ OLLAMA_HOST 未设置" -ForegroundColor Red
}
Write-Host ""

# 2. 检查进程
Write-Host "2. 检查 Ollama 进程:" -ForegroundColor Yellow
$ollamaProcess = Get-Process | Where-Object {$_.ProcessName -like "*ollama*"}
if ($ollamaProcess) {
    Write-Host "   ✓ Ollama 正在运行" -ForegroundColor Green
    $ollamaProcess | Format-Table ProcessName, Id, CPU -AutoSize
} else {
    Write-Host "   ✗ Ollama 未运行" -ForegroundColor Red
    Write-Host "   请从开始菜单启动 Ollama" -ForegroundColor Yellow
}
Write-Host ""

# 3. 检查端口监听
Write-Host "3. 检查端口 11434 监听状态:" -ForegroundColor Yellow
$listening = netstat -ano | Select-String ":11434.*LISTENING"
if ($listening) {
    Write-Host $listening -ForegroundColor White
    if ($listening -match "0\.0\.0\.0:11434") {
        Write-Host "   ✓ 正在监听所有接口 (0.0.0.0) - 可以外部访问" -ForegroundColor Green
    } elseif ($listening -match "127\.0\.0\.1:11434") {
        Write-Host "   ⚠ 只监听本地回环 (127.0.0.1) - 无法外部访问" -ForegroundColor Yellow
        Write-Host "   需要完全重启 Ollama 应用使环境变量生效" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✗ 端口 11434 未监听" -ForegroundColor Red
}
Write-Host ""

# 4. 测试 API
Write-Host "4. 测试 Ollama API:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "   ✓ API 响应正常" -ForegroundColor Green
    Write-Host "   已安装的模型:" -ForegroundColor Cyan
    $response.models | ForEach-Object { 
        Write-Host "     - $($_.name)" -ForegroundColor White
    }
} catch {
    Write-Host "   ✗ API 无响应: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "================================" -ForegroundColor Cyan
Write-Host "检查完成" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
