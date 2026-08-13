param(
    [string]$DataRoot = '/srv/cv-platform/data',
    [string]$ModelRoot = '/srv/cv-platform/models',
    [string]$PackageRoot = '/srv/cv-platform/packages'
)

$ErrorActionPreference = 'Stop'
$paths = @(
    $DataRoot,
    $ModelRoot,
    $PackageRoot,
    (Join-Path $DataRoot 'assets'),
    (Join-Path $DataRoot 'videos'),
    (Join-Path $DataRoot 'media-frames'),
    (Join-Path $ModelRoot 'faster-rcnn-resnet50'),
    (Join-Path $ModelRoot 'yolo-detector')
)
foreach ($path in $paths) {
    if (-not (Test-Path -LiteralPath $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}
Write-Output 'Server directories are ready.'
Write-Output "Faster R-CNN: $(Join-Path $ModelRoot 'faster-rcnn-resnet50')"
Write-Output "YOLO: $(Join-Path $ModelRoot 'yolo-detector')"
Write-Output 'Next: set CV_PLATFORM_ADMIN_PASSWORD, run scripts/verify.ps1, then docker compose config --quiet.'
