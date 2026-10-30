[CmdletBinding()]
param(
    [datetime]$Since = (Get-Date).AddDays(-3),
    [int]$MaxEvents = 50,
    [ValidateSet('Console', 'Json', 'Markdown', 'Html', 'All')]
    [string]$Format = 'Console',
    [string]$OutputDirectory,
    [string]$ReportName = 'power-history',
    [switch]$Json,
    [switch]$SkipPowerCfg
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($MaxEvents -lt 1) { throw '-MaxEvents must be positive.' }
if ($Json) { $Format = 'Json' }
if ($OutputDirectory -and $Format -eq 'Console') { $Format = 'All' }

$eventDefinitions = @(
    @{ LogName = 'System'; Id = 42; Category = 'Sleep' }
    @{ LogName = 'System'; Id = 107; Category = 'Resume' }
    @{ LogName = 'System'; Id = 6008; Category = 'UnexpectedShutdown' }
    @{ LogName = 'System'; Id = 41; Category = 'KernelPower' }
    @{ LogName = 'System'; Id = 1001; Category = 'Bugcheck' }
    @{ LogName = 'System'; Id = 1074; Category = 'PlannedPowerChange' }
    @{ LogName = 'System'; Id = 1; ProviderName = 'Microsoft-Windows-Power-Troubleshooter'; Category = 'Resume' }
)

$events = foreach ($definition in $eventDefinitions) {
    $filter = @{ LogName = $definition.LogName; Id = $definition.Id; StartTime = $Since }
    if ($definition.ContainsKey('ProviderName')) { $filter.ProviderName = $definition.ProviderName }
    try { Get-WinEvent -FilterHashtable $filter -MaxEvents $MaxEvents -ErrorAction Stop }
    catch [System.Diagnostics.Eventing.Reader.EventLogNotFoundException] { }
    catch {
        if ($_.Exception.Message -notmatch 'No events were found') {
            Write-Warning "Could not query event ID $($definition.Id): $($_.Exception.Message)"
        }
    }
}

$records = @($events | Sort-Object TimeCreated -Descending | Select-Object -First $MaxEvents |
    ForEach-Object {
        [pscustomobject]@{
            TimeCreated = $_.TimeCreated
            ProviderName = $_.ProviderName
            Id = $_.Id
            Category = switch ($_.Id) {
                42 { 'Sleep' }; 107 { 'Resume' }; 6008 { 'UnexpectedShutdown' }
                41 { 'KernelPower' }; 1001 { 'Bugcheck' }; 1074 { 'PlannedPowerChange' }
                default { 'PowerTroubleshooterResume' }
            }
            Message = ($_.Message -replace '\s+', ' ').Trim()
        }
    })

$powerCfg = [ordered]@{}
if (-not $SkipPowerCfg) {
    foreach ($query in @('lastwake', 'waketimers', 'requests')) {
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $powerCfgOutput = @(powercfg "/$query" 2>&1)
        $powerCfg[$query] = ($powerCfgOutput -join [Environment]::NewLine).Trim()
        $ErrorActionPreference = $previousErrorAction
    }
}

$result = [pscustomobject]@{
    ComputerName = $env:COMPUTERNAME
    Since = $Since
    GeneratedAt = Get-Date
    Events = $records
    PowerCfg = $powerCfg
}

function ConvertTo-MarkdownReport {
    param([pscustomobject]$Report)
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add('# Windows power history')
    $lines.Add('')
    $lines.Add("- Computer: **$($Report.ComputerName)**")
    $lines.Add("- Since: **$($Report.Since)**")
    $lines.Add("- Generated: **$($Report.GeneratedAt)**")
    $lines.Add("- Matching events: **$($Report.Events.Count)**")
    $lines.Add('')
    $lines.Add('## Events')
    $lines.Add('')
    $lines.Add('| Time | Category | Provider | ID | Message |')
    $lines.Add('|---|---|---|---:|---|')
    foreach ($event in $Report.Events) {
        $message = ($event.Message -replace '\|', '\\|')
        $lines.Add("| $($event.TimeCreated) | $($event.Category) | $($event.ProviderName) | $($event.Id) | $message |")
    }
    if ($Report.Events.Count -eq 0) { $lines.Add('| — | No matching events | — | — | — |') }
    $lines.Add('')
    $lines.Add('## powercfg state')
    $lines.Add('')
    foreach ($query in $Report.PowerCfg.Keys) {
        $lines.Add("### /$query")
        $lines.Add('')
        $lines.Add('```text')
        $lines.Add($Report.PowerCfg[$query])
        $lines.Add('```')
        $lines.Add('')
    }
    $lines -join [Environment]::NewLine
}

function ConvertTo-HtmlReport {
    param([pscustomobject]$Report)
    $eventRows = foreach ($event in $Report.Events) {
        $time = [System.Net.WebUtility]::HtmlEncode([string]$event.TimeCreated)
        $category = [System.Net.WebUtility]::HtmlEncode([string]$event.Category)
        $provider = [System.Net.WebUtility]::HtmlEncode([string]$event.ProviderName)
        $message = [System.Net.WebUtility]::HtmlEncode([string]$event.Message)
        "<tr><td>$time</td><td>$category</td><td>$provider</td><td>$($event.Id)</td><td>$message</td></tr>"
    }
    if (-not $eventRows) { $eventRows = '<tr><td colspan="5">No matching events.</td></tr>' }
    $powerSections = foreach ($query in $Report.PowerCfg.Keys) {
        $text = [System.Net.WebUtility]::HtmlEncode([string]$Report.PowerCfg[$query])
        "<h3>/$query</h3><pre>$text</pre>"
    }
    @"
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Windows power history</title>
<style>body{font:16px system-ui,sans-serif;max-width:1400px;margin:2rem auto;padding:0 1rem;color:#202124}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:.45rem;text-align:left;vertical-align:top}th{background:#eee}pre{background:#f5f5f5;padding:1rem;white-space:pre-wrap}</style>
</head><body><h1>Windows power history</h1>
<ul><li>Computer: <strong>$($Report.ComputerName)</strong></li><li>Since: <strong>$($Report.Since)</strong></li><li>Generated: <strong>$($Report.GeneratedAt)</strong></li><li>Matching events: <strong>$($Report.Events.Count)</strong></li></ul>
<h2>Events</h2><table><thead><tr><th>Time</th><th>Category</th><th>Provider</th><th>ID</th><th>Message</th></tr></thead><tbody>$($eventRows -join '')</tbody></table>
<h2>powercfg state</h2>$($powerSections -join '')</body></html>
"@
}

function Write-ReportFiles {
    param([pscustomobject]$Report)
    if (-not $OutputDirectory) { throw '-OutputDirectory is required for file reports.' }
    if ($ReportName -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') { throw '-ReportName contains unsupported characters.' }
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
    $jsonPath = Join-Path $OutputDirectory "$ReportName.json"
    $markdownPath = Join-Path $OutputDirectory "$ReportName.md"
    $htmlPath = Join-Path $OutputDirectory "$ReportName.html"
    if ($Format -in @('Json', 'All')) { $Report | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $jsonPath }
    if ($Format -in @('Markdown', 'All')) { ConvertTo-MarkdownReport $Report | Set-Content -Encoding utf8 $markdownPath }
    if ($Format -in @('Html', 'All')) { ConvertTo-HtmlReport $Report | Set-Content -Encoding utf8 $htmlPath }
    [pscustomobject]@{ Json = $jsonPath; Markdown = $markdownPath; Html = $htmlPath }
}

if ($Format -eq 'Console') {
    'Power history'
    '============='
    "Computer: $($result.ComputerName)"
    "Since:    $($result.Since)"
    "Events:   $($records.Count)"
    ''
    if ($records.Count -eq 0) { 'No matching events were found.' }
    else { $records | Format-List | Out-String | Write-Output }
    if (-not $SkipPowerCfg) {
        'powercfg state'
        '==============='
        foreach ($query in $powerCfg.Keys) { "[$query]"; $powerCfg[$query] }
    }
}
else {
    $paths = Write-ReportFiles $result
    $paths | Format-List | Out-String | Write-Output
}
