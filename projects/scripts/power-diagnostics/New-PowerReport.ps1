[CmdletBinding()]
param(
    [int]$Days = 3,
    [int]$MaxEvents = 100,
    [string]$OutputDirectory = (Join-Path (Get-Location) 'power-reports'),
    [switch]$SkipPowerCfg
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Days -lt 1) { throw '-Days must be positive.' }
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportDirectory = Join-Path $OutputDirectory $timestamp
$collector = Join-Path $PSScriptRoot 'Get-PowerHistory.ps1'

& $collector -Since (Get-Date).AddDays(-$Days) -MaxEvents $MaxEvents -Format All `
    -OutputDirectory $reportDirectory -SkipPowerCfg:$SkipPowerCfg

Write-Output "Report directory: $reportDirectory"
