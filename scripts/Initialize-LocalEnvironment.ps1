$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$environmentPath = Join-Path $projectDirectory '.env'

if (Test-Path -LiteralPath $environmentPath) {
    Write-Output '.env already exists; its values were preserved.'
    exit 0
}

function New-LocalSecret {
    $bytes = New-Object byte[] 32
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
        return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $generator.Dispose()
    }
}

$environmentLines = @(
    "DJANGO_SECRET_KEY=$(New-LocalSecret)"
    "POSTGRES_PASSWORD=$(New-LocalSecret)"
    'POSTGRES_DB=docinsight'
    'POSTGRES_USER=docinsight'
    'DB_HOST_PORT=5432'
    'BACKEND_PORT=8000'
    'FRONTEND_PORT=5173'
)
[System.IO.File]::WriteAllLines($environmentPath, $environmentLines, (New-Object System.Text.UTF8Encoding $false))
Write-Output 'Created .env with generated local secrets. Secret values were not displayed.'

