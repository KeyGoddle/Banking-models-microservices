Write-Host "=== Testing Model A ===" -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://127.0.0.1:8001/predict" -Method POST `
  -Body (Get-Content "test_model_a.json" -Raw) `
  -ContentType "application/json" | ConvertTo-Json -Depth 8

Write-Host "`n=== Testing Model B ===" -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://127.0.0.1:8002/predict" -Method POST `
  -Body (Get-Content "test_model_b.json" -Raw) `
  -ContentType "application/json" | ConvertTo-Json -Depth 8

Write-Host "`n=== Testing Orchestrator ===" -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST `
  -Body (Get-Content "test_orchestrator.json" -Raw) `
  -ContentType "application/json" | ConvertTo-Json -Depth 8
