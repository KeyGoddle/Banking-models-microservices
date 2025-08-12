$body = @{
  client = @{
    age = 32; income_monthly = 180000; tenure_months = 26;
    has_mortgage = $true; active_loans = 1; monthly_obligations = 45000; region = "RU-MOW"
  };
  transactions = @(
    @{ amount=3500; currency="RUB"; mcc=5411; country="RU"; unix_ts=1723300000; channel="card_present" },
    @{ amount=98000; currency="RUB"; mcc=6011; country="TR"; unix_ts=1723303600; channel="card_not_present" }
  )
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 8