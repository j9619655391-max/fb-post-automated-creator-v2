$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:8000'
$login = Invoke-RestMethod -Uri "$base/api/v1/auth/login" -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ username = 'local_smoke_user'; password = 'LocalSmokePass_2026!' }
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$orgs = @(Invoke-RestMethod -Uri "$base/api/v1/organizations/" -Headers $headers)
if ($orgs.Count -lt 1) { throw 'No local organization is available' }
$existing = $orgs[0]
$members = @(Invoke-RestMethod -Uri "$base/api/v1/organizations/$($existing.id)/members" -Headers $headers)
if ($members.Count -lt 1) { throw 'Existing organization has no owner/member record' }
$stamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$createBody = @{ name = "Local Probe $stamp"; slug = "local-probe-$stamp" } | ConvertTo-Json
$created = Invoke-RestMethod -Uri "$base/api/v1/organizations/" -Method Post -Headers $headers -ContentType 'application/json' -Body $createBody
if (-not $created.id) { throw 'Organization create did not return an id' }
Write-Output "Organization API smoke: PASS (list, members, create; created_id=$($created.id))"
