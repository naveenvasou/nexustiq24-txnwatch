import json
import os
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(
    title="TxnWatch",
    description="Track 6 - Banking: Transaction Risk Investigation"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RULES_PATH = os.path.join(DATA_DIR, "risk_rules.txt")


def load_rules() -> str:
    """Loads the static bank risk rules document."""
    try:
        if os.path.exists(RULES_PATH):
            with open(RULES_PATH, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    return ""


def load_sample_customers() -> Dict[str, Any]:
    """Loads pre-generated sample customer transaction records."""
    samples = {}
    for filename in ["customer_101.json", "customer_102.json"]:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    cust_data = json.load(f)
                    samples[cust_data["customer_id"]] = cust_data
            except Exception:
                pass
    return samples


@app.get("/api/rules")
def get_rules():
    return {"rules": load_rules()}


@app.get("/api/customers")
def get_customers():
    return {"customers": load_sample_customers()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
