# TrustLens AI — Start Backend
Write-Host "Starting TrustLens AI Backend..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\backend"

$PythonPath = "python"
# Check if python command points to Microsoft's redirect stub
$test = & python --version 2>&1
if ($test -match "Python was not found" -or $test -match "install from the Microsoft Store") {
    # Search for the actual Microsoft Store Python installation dynamically
    $StorePython = Get-ChildItem -Path "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.*" -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
    if ($StorePython) {
        $PythonPath = $StorePython
    } else {
        Write-Host "WARNING: Microsoft Store Python not found. Trying default 'python' command anyway." -ForegroundColor Yellow
    }
}

Write-Host "Using Python: $PythonPath" -ForegroundColor Yellow
& $PythonPath -m uvicorn main:app --reload --port 8000
