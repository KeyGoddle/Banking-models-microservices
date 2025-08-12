from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import statistics, time, math

app = FastAPI(title="Model A - Fraud/Anomaly", version="1.2.0")

# Простые доменные списки
HI_RISK_COUNTRIES = {"TR","CN","NG","UA","AE"}       # пример
RISKY_MCC = {4829, 6011, 7995}                       # remittance, cash advance, betting
NIGHT_HOURS = set(list(range(0,6)) + [23])           # ночь

class Tx(BaseModel):
    amount: float
    currency: str
    mcc: int
    country: str
    unix_ts: int
    channel: str   # "card_present" / "card_not_present" / "pos" / "online"

class Client(BaseModel):
    age: int
    income_monthly: float
    tenure_months: int
    has_mortgage: bool
    active_loans: int
    monthly_obligations: float
    region: Optional[str] = None

class RequestIn(BaseModel):
    client: Client
    transactions: List[Tx] = Field(default_factory=list)

@app.get("/")
def root():
    return {"service":"model_a","status":"ok"}

@app.get("/healthz")
def health():
    return {"status":"ok"}

def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

@app.post("/predict")
def predict(req: RequestIn):
    txs = req.transactions
    if not txs:
        return {"anomaly_score": 0.0, "reasons": ["No transactions"], "features": {}}

    amounts = [max(0.0, t.amount) for t in txs]
    avg = statistics.mean(amounts)
    stdev = statistics.pstdev(amounts) or 1.0
    last = max(txs, key=lambda t: t.unix_ts)

    # Признаки
    hi_risk_country = int(any(t.country in HI_RISK_COUNTRIES for t in txs))
    risky_mcc = int(any(t.mcc in RISKY_MCC for t in txs))
    night_ratio = sum(time.gmtime(t.unix_ts).tm_hour in NIGHT_HOURS for t in txs) / len(txs)
    z_amount = (last.amount - avg) / stdev
    velocity_1h = sum((last.unix_ts - t.unix_ts) <= 3600 for t in txs)

    # аккумулируем факторы риска
    logit = -0.6 + (
        0.8*hi_risk_country +
        0.6*risky_mcc +
        0.5*night_ratio +
        0.35*max(0.0, z_amount) +
        0.25*max(0, velocity_1h-3) +
        (0.2 if last.channel.lower() in {"card_not_present","online"} else 0.0)
    )
    anomaly = round(sigmoid(logit), 3)

    reasons = []
    if hi_risk_country: reasons.append("High-risk country")
    if risky_mcc: reasons.append("Risky MCC")
    if night_ratio > 0.3: reasons.append("Night activity")
    if z_amount > 1.2: reasons.append("Unusual amount vs profile")
    if velocity_1h > 3: reasons.append("Velocity spike")
    if last.channel.lower() in {"card_not_present","online"}: reasons.append("CNP/online channel")

    return {
        "anomaly_score": anomaly,
        "reasons": reasons or ["Normal pattern"],
        "features": {
            "avg_amount": round(avg,2),
            "z_amount": round(z_amount,2),
            "night_ratio": round(night_ratio,2),
            "hi_risk_country": hi_risk_country,
            "risky_mcc": risky_mcc,
            "velocity_1h": velocity_1h,
            "last_channel": last.channel
        }
    }
