# Runs the Paper 1A H2 ablation batch on Windows with Docker Desktop.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python run_h2.py --dry-run
python run_h2.py --execute --mode docker --ablation all --runs 5 --yes
python run_h2.py --execute --mode docker --ablation all --runs 2 --sham --yes
python summarise.py
Write-Host "Done. See RESULTS.md and results\"
