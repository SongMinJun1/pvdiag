param(
    [Parameter(Mandatory=$true)][string]$IngestRoot,
    [Parameter(Mandatory=$true)][string]$SnapshotRoot,
    [int]$StableMinutes = 10,
    [string]$Sites = "conalog,gangui,ktc_ess",
    [string]$Pattern = "*.csv"
)

$siteList = $Sites.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
$cutoff = (Get-Date).AddMinutes(-1 * $StableMinutes)
$copiedCount = 0
$skippedRecentCount = 0

foreach ($site in $siteList) {
    $candidates = @(
        (Join-Path $IngestRoot "$site\raw"),
        (Join-Path $IngestRoot "data\$site\raw")
    )
    $sourceDir = $null
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $sourceDir = $candidate
            break
        }
    }
    if (-not $sourceDir) {
        throw "source raw dir not found for site=$site under $IngestRoot"
    }

    $targetDir = Join-Path $SnapshotRoot "$site\raw"
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    Get-ChildItem $sourceDir -Filter $Pattern | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
        $sourceFile = $_.FullName
        $targetFile = Join-Path $targetDir $_.Name
        $tempFile = "$targetFile.__copying__"

        if ($_.LastWriteTime -gt $cutoff) {
            $script:skippedRecentCount += 1
            return
        }

        Copy-Item $sourceFile -Destination $tempFile -Force
        Move-Item $tempFile $targetFile -Force
        $script:copiedCount += 1
    }
}

Write-Host "[OK] snapshot copy completed"
Write-Host "[OK] copied_count=$copiedCount"
Write-Host "[OK] skipped_recent_count=$skippedRecentCount"
Write-Host "[OK] snapshot_root=$SnapshotRoot"
