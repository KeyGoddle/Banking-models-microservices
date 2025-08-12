from datetime import datetime, timedelta
import json, os, requests
from airflow import DAG
from airflow.operators.python import PythonOperator

ORCH_URL = os.getenv("ORCH_URL", "http://127.0.0.1:8000/analyze")

def sample_payload():
    return {
        "client": {
            "age": 32, "income_monthly": 180000, "tenure_months": 26,
            "has_mortgage": True, "active_loans": 1, "monthly_obligations": 45000, "region": "RU-MOW"
        },
        "transactions": [
            {"amount": 3500, "currency":"RUB", "mcc":5411, "country":"RU", "unix_ts":1723300000, "channel":"card_present"},
            {"amount": 98000, "currency":"RUB", "mcc":6011, "country":"TR", "unix_ts":1723303600, "channel":"card_not_present"}
        ]
    }

def call_orchestrator(**_):
    body = sample_payload()
    r = requests.post(ORCH_URL, json=body, timeout=10)
    r.raise_for_status()
    res = r.json()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    # (optional) push to XCom or write to file/store
    return res.get("decision", {}).get("status")

default_args = {"owner": "ml", "retries": 1, "retry_delay": timedelta(minutes=1)}
with DAG(
    "model_orchestration_demo",
    default_args=default_args,
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["demo","mlops"]
) as dag:
    run = PythonOperator(task_id="call_orchestrator", python_callable=call_orchestrator)