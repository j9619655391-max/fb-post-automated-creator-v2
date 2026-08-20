$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:8000'

$root = Invoke-WebRequest -Uri "$base/" -UseBasicParsing
if ($root.StatusCode -ne 200) { throw "Root endpoint returned $($root.StatusCode)" }
$docs = Invoke-WebRequest -Uri "$base/docs" -UseBasicParsing
if ($docs.StatusCode -ne 200) { throw "Docs endpoint returned $($docs.StatusCode)" }

$username = 'local_smoke_user'
$email = 'local_smoke_user@example.com'
$password = 'LocalSmokePass_2026!'
$signupBody = @{ username = $username; email = $email; full_name = 'Local Smoke User'; password = $password } | ConvertTo-Json
try {
    Invoke-RestMethod -Uri "$base/api/v1/auth/signup" -Method Post -ContentType 'application/json' -Body $signupBody | Out-Null
} catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 400) { throw }
}

$login = Invoke-RestMethod -Uri "$base/api/v1/auth/login" -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ username = $username; password = $password }
if (-not $login.access_token) { throw 'Login did not return an access token' }

$me = Invoke-RestMethod -Uri "$base/api/v1/users/me" -Method Get -Headers @{ Authorization = "Bearer $($login.access_token)" }
if ($me.username -ne $username) { throw 'Authenticated user response did not match smoke user' }

Write-Output 'HTTP smoke: PASS (root, docs, signup/login, authenticated user)'
