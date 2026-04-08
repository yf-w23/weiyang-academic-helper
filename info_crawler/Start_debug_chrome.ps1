$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profileDir = "$env:TEMP\chrome_debug_profile"

if (-not (Test-Path $chromePath)) {
    $chromePath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
}

if (-not (Test-Path $chromePath)) {
    Write-Host "未找到 Chrome，请修改脚本中的路径" -ForegroundColor Red
    pause
    exit
}

# 先杀掉已有的调试进程（避免端口冲突）
$proc = Get-Process | Where-Object { $_.ProcessName -like "*chrome*" -and $_.CommandLine -like "*remote-debugging-port=9222*" } -ErrorAction SilentlyContinue
if ($proc) {
    Stop-Process -Id $proc.Id -Force
    Start-Sleep -Seconds 1
}

Start-Process -FilePath $chromePath -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=`"$profileDir`"", "--new-window", "https://www.google.com"

Write-Host "`n独立调试 Chrome 已启动！" -ForegroundColor Green
Write-Host "远程调试地址: http://127.0.0.1:9222/json"
Write-Host "请在此窗口中登录目标网站，登录完成后告诉我。" -ForegroundColor Cyan