# KL2 Well Data Sync — Windows -> VPS
# Run this in PowerShell on your Windows machine as Administrator
# Requires: OpenSSH client (built into Windows 10/11)

$VPS_IP      = "72.62.71.199"
$VPS_USER    = "ariffazil"
$WINDOWS_SRC = "C:\Users\arif.fazil\OneDrive - Enterprise\Documents\MY DOCUMENTS\1. Enterprise Work\1. Projects\31. KINABALU BASIN\03. Well\DSGLink"
$VPS_DEST    = "${VPS_USER}@${VPS_IP}:/root/geox/data/kl2/wells/"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "KL2 Well Data Sync to VPS" -ForegroundColor Cyan
Write-Host "============================================================"
Write-Host "Source : $WINDOWS_SRC"
Write-Host "Dest   : $VPS_DEST"
Write-Host ""

# Check source exists
if (-not (Test-Path $WINDOWS_SRC)) {
    Write-Error "Source path not found: $WINDOWS_SRC"
    exit 1
}

# Show files to sync
$files = Get-ChildItem $WINDOWS_SRC -Include "*.las","*.csv","*.txt" -Recurse | Select -ExpandProperty FullName
Write-Host "Found $($files.Count) LAS/CSV/TXT files"
$files | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" }
if ($files.Count -gt 10) { Write-Host "  ... and $($files.Count - 10) more" }
Write-Host ""

# Sync command using scp (recursive)
Write-Host "Starting SCP transfer..." -ForegroundColor Yellow
Write-Host "scp -r -o StrictHostKeyChecking=no `"$WINDOWS_SRC\*`" `"$VPS_DEST`""
scp -r -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null `"$WINDOWS_SRC\*`" "$VPS_DEST"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSUCCESS — Data synced to VPS at /root/geox/data/kl2/wells/" -ForegroundColor Green
    Write-Host "GEOX container path: /app/data/kl2/wells/" -ForegroundColor Green
} else {
    Write-Error "SCP failed. If password auth, ensure you type the VPS password when prompted."
    Write-Host "Alternative (if ssh key auth):"
    Write-Host "  scp -r `"$WINDOWS_SRC\*`" ${VPS_USER}@${VPS_IP}:/root/geox/data/kl2/wells/"
}
