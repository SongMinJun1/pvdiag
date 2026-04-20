param(
    [Parameter(Mandatory=$true)][string]$ArchiveRoot,
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [int]$WindowDays = 120,
    [string]$Sites = "conalog,gangui,ktc_ess"
)

$siteList = $Sites.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
$cutoff = (Get-Date).AddDays(-1 * $WindowDays)

foreach ($site in $siteList) {
    $candidates = @(
        (Join-Path $ArchiveRoot "$site\raw"),
        (Join-Path $ArchiveRoot "$site\raw_all"),
        (Join-Path $ArchiveRoot "data\$site\raw"),
        (Join-Path $ArchiveRoot "data\$site\raw_all")
    )
    $sourceDir = $null
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $sourceDir = $candidate
            break
        }
    }
    if (-not $sourceDir) {
        throw "source raw dir not found for site=$site under $ArchiveRoot"
    }

    $targetDir = Join-Path $RuntimeRoot "$site\raw"
    if (Test-Path $targetDir) {
        Remove-Item $targetDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    Get-ChildItem $sourceDir -Filter *.csv | ForEach-Object {
        if ($_.Name -match '(\d{4}-\d{2}-\d{2})') {
            $day = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd', $null)
            if ($day -ge $cutoff) {
                Copy-Item $_.FullName -Destination $targetDir
            }
        }
    }
}

Write-Host "[OK] staged recent raw files into $RuntimeRoot"
