param(
  [string]$Source = "$env:USERPROFILE\Desktop\ErrandBuddy-main",
  [string]$Repo   = "$env:USERPROFILE\Desktop\ErrandBuddy",
  [string]$Branch = 'feature/sync-workspace',
  [string]$Message = 'chore(sync): update from local workspace',
  [switch]$SnapshotTag,
  [switch]$Push
)

$ErrorActionPreference = 'Stop'
$env:Path += ';C:\\Program Files\\Git\\cmd'

if (-not (Test-Path $Source)) { throw "Source not found: $Source" }
if (-not (Test-Path (Join-Path $Repo '.git'))) { throw "Repo not found (no .git): $Repo" }

$excludeDirs = @('.git','.vscode','__pycache__','.venv*','venv','env')
$excludeFiles = @('*.pyc','*.pyo','*.pyd','*.sqlite3','*.db','*.log')

# Mirror workspace into repo using robocopy
$xd = @(); foreach ($d in $excludeDirs) { $xd += '/XD'; $xd += (Join-Path $Source $d); $xd += (Join-Path $Repo $d); $xd += $d }
$xf = @(); foreach ($f in $excludeFiles) { $xf += '/XF'; $xf += $f }
$roboArgs = @($Source,$Repo,'/MIR','/NFL','/NDL','/NJH','/NJS','/NP','/R:1','/W:1') + $xd + $xf
$rob = Start-Process -FilePath robocopy -ArgumentList $roboArgs -Wait -PassThru
# Robocopy exit codes 0-7 are success
if ($rob.ExitCode -gt 7) { throw "robocopy failed with exit code $($rob.ExitCode)" }

Push-Location $Repo

# Ensure branch exists and is current
$haveLocal = (git show-ref --verify --quiet "refs/heads/$Branch"); $haveLocal = ($LASTEXITCODE -eq 0)
$haveRemote = (git ls-remote --exit-code --heads origin $Branch *> $null); $haveRemote = ($LASTEXITCODE -eq 0)
if (-not $haveLocal) {
  if ($haveRemote) { git checkout -b $Branch origin/$Branch | Out-Null }
  else { git checkout -b $Branch | Out-Null }
} else { git checkout $Branch | Out-Null }

# Fast-forward from remote if it exists
if ($haveRemote) { git pull --ff-only origin $Branch | Out-Null }

# Stage and commit changes if any
$porcelain = git status --porcelain
if ($porcelain) {
  git add -A
  $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
  $fullMsg = "$Message ($stamp)"
  git commit -m $fullMsg | Out-Null
  $changed = (git show --name-status --oneline -1)
  Write-Output "Committed changes:"; Write-Output $changed
  if ($SnapshotTag) {
    $tagName = "snapshot-" + (Get-Date -Format 'yyyyMMdd-HHmmss')
    git tag -a $tagName -m "Snapshot after sync $stamp"
    Write-Output "Created tag: $tagName"
  }
  if ($Push) {
    git push -u origin $Branch | Out-Null
    if ($SnapshotTag) { git push --tags | Out-Null }
    Write-Output "Pushed $Branch to origin"
  }
} else {
  Write-Output 'No changes to commit.'
}

Pop-Location
