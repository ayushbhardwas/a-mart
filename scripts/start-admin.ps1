$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

function Get-PythonCommand {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    return [pscustomobject]@{ Exe = "py"; Args = @("-3") }
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    return [pscustomobject]@{ Exe = "python"; Args = @() }
  }

  return $null
}

$pythonCommand = Get-PythonCommand

if (-not $pythonCommand) {
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if (-not $winget) {
    throw "Python is not installed and winget was not found. Install Python 3 from https://www.python.org/downloads/ and run this script again."
  }

  Write-Host "Python was not found. Installing Python using winget..."
  winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
  $pythonCommand = Get-PythonCommand
}

if (-not $pythonCommand) {
  throw "Python installation was not found after setup. Restart PowerShell and run scripts\start-admin.ps1 again."
}

Write-Host "Starting A-Mart local editor..."
Write-Host "Open http://127.0.0.1:9000/admin/"
& $pythonCommand.Exe @($pythonCommand.Args) tools\admin_server.py
