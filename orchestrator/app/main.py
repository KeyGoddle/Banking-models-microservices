from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import asyncio
import httpx
import uuid
import json
import logging
from fastapi.responses import RedirectResponse
# -------------------------
# App & config
# -------------------------
app = FastAPI(title="Orchestrator", version="1.2.0")


@app.get("/")
async def root():
    return RedirectResponse(url="/docs", status_code=302)
@app.get("/info")
async def info():
    return {"service": "orchestrator", "status": "ok"}
MODEL_A_URL = os.getenv("MODEL_A_URL", "http://model_a:8001/predict")
MODEL_B_URL = os.getenv("MODEL_B_URL", "http://model_b:8002/predict")

# decision thresholds 
THR_REVIEW = float(os.getenv("FRAUD_T_REVIEW", "0.35"))
THR_DECLINE = float(os.getenv("FRAUD_T_DECLINE", "0.7"))
THR_PD_MAX_FOR_APPROVE = float(os.getenv("PD_MAX_FOR_APPROVE", "0.25"))

# Kafka 
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "scored_events")
_KAFKA_PRODUCER = None
if KAFKA_BOOTSTRAP:
    try:
        from confluent_kafka import Producer  # type: ignore
        _KAFKA_PRODUCER = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})
    except Exception as e:
        logging.warning(f"Kafka disabled: {e}")
        _KAFKA_PRODUCER = None

# -------------------------
# Schemas
# -------------------------
class Tx(BaseModel):
    amount: float
    currency: str
    mcc: int
    country: str
    unix_ts: int
    channel: str

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

# -------------------------
# Health
# -------------------------
@app.get("/healthz")
async def health():
    return {"status": "ok"}

# -------------------------
# Utils
# -------------------------
async def call_model(url: str, payload: dict):
    timeout = httpx.Timeout(5.0, connect=2.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()

def _kafka_send(obj: dict):
    """Best-effort отправка результата в Kafka."""
    if not _KAFKA_PRODUCER:
        return
    try:
        _KAFKA_PRODUCER.produce(KAFKA_TOPIC, json.dumps(obj, ensure_ascii=False).encode("utf-8"))
        _KAFKA_PRODUCER.flush(1.0)
    except Exception as e:
        logging.warning(f"Kafka produce failed: {e}")

# -------------------------
# Main handler
# -------------------------
@app.post("/analyze")
async def analyze(inp: RequestIn):
    trace_id = str(uuid.uuid4())

    payload_a = {
        "client": inp.client.model_dump(),
        "transactions": [t.model_dump() for t in inp.transactions],
    }
    payload_b = {"client": inp.client.model_dump()}

    try:
        # Параллельные вызовы моделей
        res_a, res_b = await asyncio.gather(
            call_model(MODEL_A_URL, payload_a),
            call_model(MODEL_B_URL, payload_b),
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Model call failed: {e}")

    # Достаём ключевые метрики из ответов моделей
    anomaly = float(res_a.get("anomaly_score", 0.0))
    pd = float(res_b.get("pd_score", 0.5))
    limit = int(res_b.get("limit_suggestion", 0))

    # Политика принятия решения
    status = "approve"
    explain: List[str] = []

    if anomaly >= THR_DECLINE:
        status = "decline"
        explain.append(f"anomaly_score>={THR_DECLINE}")
    elif anomaly >= THR_REVIEW:
        status = "review"
        explain.append(f"anomaly_score>={THR_REVIEW}")

    if pd > THR_PD_MAX_FOR_APPROVE and status == "approve":
        status = "review"
        explain.append(f"pd_score>{THR_PD_MAX_FOR_APPROVE}")

    if status == "approve" and limit <= 0:
        status = "review"
        explain.append("no viable limit")

    result = {
        "trace_id": trace_id,
        "model_fraud": res_a,
        "model_risk": res_b,
        "decision": {
            "status": status,
            "explain": "; ".join(explain) if explain else "OK",
            "policy": {
                "fraud_threshold_review": THR_REVIEW,
                "fraud_threshold_decline": THR_DECLINE,
                "pd_max_for_approve": THR_PD_MAX_FOR_APPROVE,
            },
        },
    }

    
    _kafka_send(result)

    return result
