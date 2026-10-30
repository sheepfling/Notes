param(
    [ValidateSet("auto", "numpy", "cupy")]
    [string]$Backend = "auto",
    [ValidateSet("numpy", "numba")]
    [string]$ReactionBackend = "numpy",
    [string]$Python = "python",
    [string]$OutputRoot = "artifacts\converging-flow\scripted-run",
    [switch]$FullResolution,
    [switch]$NoPlots
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repositoryRoot

$arguments = @(
    "-m", "converging_flow.runner",
    "--backend", $Backend,
    "--reaction-backend", $ReactionBackend,
    "--output-root", $OutputRoot
)
if ($FullResolution) { $arguments += "--full-resolution" }
if ($NoPlots) { $arguments += "--no-plots" }

& $Python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "converging-flow runner failed with exit code $LASTEXITCODE"
}
