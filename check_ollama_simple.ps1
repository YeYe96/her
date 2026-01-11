Write-Host "=== Ollama Check ===" -ForegroundColor Cyan

Write-Host "`n1. Environment Variable:" -ForegroundColor Yellow
$env:OLLAMA_HOST
[System.Environment]::GetEnvironmentVariable('OLLAMA_HOST', 'User')

Write-Host "`n2. Ollama Process:" -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*ollama*"} | Format-Table ProcessName, Id -AutoSize

Write-Host "`n3. Port Listening:" -ForegroundColor Yellow
netstat -ano | Select-String ":11434.*LISTENING"

Write-Host "`n4. API Test:" -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get | Select-Object -ExpandProperty models | Format-Table name
} catch {
    Write-Host "API Error: $_" -ForegroundColor Red
}
