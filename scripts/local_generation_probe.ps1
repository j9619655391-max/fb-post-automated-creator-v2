$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:8000'
$login = Invoke-RestMethod -Uri "$base/api/v1/auth/login" -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ username = 'local_smoke_user'; password = 'LocalSmokePass_2026!' }
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$stamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$body = @{ category_name = 'Business'; organization_id = 2; idempotency_key = "local-generation-probe-$stamp" } | ConvertTo-Json
try {
    Invoke-RestMethod -Uri "$base/api/v1/generation/draft" -Method Post -Headers $headers -ContentType 'application/json' -Body $body | Out-Null
    throw 'Generation unexpectedly succeeded without GEMINI_API_KEY'
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    if ($status -ne 503) {
        throw "Unexpected generation status: $status"
    }
    Write-Output 'Generation configuration gate: PASS (503; add GEMINI_API_KEY to enable AI drafts)'
}
