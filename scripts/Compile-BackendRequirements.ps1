# Compile application requirements using the locked toolchain in a disposable
# Linux container. No Python packages are installed on the Windows host.
param(
    [string]$CertificateBundlePath
)

$ErrorActionPreference = 'Stop'
$backendDirectory = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../backend')).Path
$certificateArguments = @()
if ($CertificateBundlePath) {
    $resolvedCertificatePath = (Resolve-Path -LiteralPath $CertificateBundlePath).Path
    $certificateArguments = @(
        '--mount', "type=bind,source=$resolvedCertificatePath,target=/tmp/pip-ca.pem,readonly",
        '--env', 'PIP_CERT=/tmp/pip-ca.pem'
    )
}
$compileScript = @'
python -m venv /opt/lock-venv
/opt/lock-venv/bin/python -m pip install --no-cache-dir --require-hashes -r requirements-tools.txt
/opt/lock-venv/bin/python -m pip check
/opt/lock-venv/bin/python -m site
cat /opt/lock-venv/pyvenv.cfg
/opt/lock-venv/bin/pip-compile --quiet --generate-hashes --resolver=backtracking --output-file=requirements.txt requirements.in
'@

& docker run --rm `
    @certificateArguments `
    --mount "type=bind,source=$backendDirectory,target=/work" `
    --workdir /work `
    --env 'CUSTOM_COMPILE_COMMAND=./scripts/Compile-BackendRequirements.ps1' `
    python:3.13.15-slim-bookworm sh -ec $compileScript
if ($LASTEXITCODE -ne 0) {
    throw "Dependency compilation failed (exit $LASTEXITCODE). Review requirements.txt before building."
}
