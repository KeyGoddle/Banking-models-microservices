from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import math

app = FastAPI(title="Model B - Credit Risk", version="1.2.0")

class Client(BaseModel):
    age: int
    income_monthly: float
    tenure_months: int
    has_mortgage: bool
    active_loans: int
    monthly_obligations: float
    region: Optional[str] = None

@app.get("/")
def root():
    return {"service":"model_b","status":"ok"}

@app.get("/healthz")
def health():
    return {"status":"ok"}

def clamp(x, lo, hi): return max(lo, min(hi, x))
def sigmoid(x): return 1 / (1 + math.exp(-x))

@app.post("/predict")
def predict(req: dict):
    c = Client(**req.get("client", req))  # поддержим и {"client":{...}}, и просто {...}

    dti = c.monthly_obligations / max(1.0, c.income_monthly)
    age_factor = 0.5 if c.age < 25 else 0.0
    short_tenure = int(c.tenure_months < 12)
    many_loans = int(c.active_loans >= 3)

    logit = -2.2 \
            + 2.0*clamp(dti,0,1.5) \
            + 0.7*age_factor \
            + 0.6*short_tenure \
            + 0.4*many_loans \
            - 0.3*int(c.has_mortgage)

    pd = round(sigmoid(logit), 3)
    bucket = "A" if pd < 0.1 else "B" if pd < 0.2 else "C" if pd < 0.35 else "D" if pd < 0.6 else "E"

    base_limit = c.income_monthly * (0.3 - 0.2*pd)     # ниже PD → выше коэффициент
    limit = int(max(0, base_limit - c.monthly_obligations*2))

    reasons = []
    reasons.append(f"DTI={round(dti,2)} {'OK' if dti<0.35 else 'High'}")
    if short_tenure: reasons.append("Short tenure")
    if many_loans: reasons.append("Multiple active loans")
    if c.age < 23: reasons.append("Very young")
    if c.has_mortgage: reasons.append("Has mortgage (stability)")

    return {
        "pd_score": pd,
        "bucket": bucket,
        "limit_suggestion": limit,
        "reasons": reasons
    }
