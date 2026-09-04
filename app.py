import json
import os
from typing import Any, Dict
from fastapi import FastAPI, Request
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


def run_investigation(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "GEMINI_API_KEY environment variable is not set. Set GEMINI_API_KEY to run live investigations."
        }

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        # Dump entire risk rules document directly into the prompt without retrieval/embeddings
        all_rules = load_rules()

        prompt = f"""You are a bank transaction risk investigator assistant.
Below is the bank's transaction risk rules document:
----------------------------------------
{all_rules}
----------------------------------------

Below is the customer profile and transaction history under review:
----------------------------------------
Customer ID: {customer_data.get('customer_id', 'Unknown')}
Customer Name: {customer_data.get('customer_name', 'Unknown')}
Account Type: {customer_data.get('account_type', 'Unknown')}
KYC Tier: {customer_data.get('kyc_tier', 'Unknown')}

Transactions:
{json.dumps(customer_data.get('transactions', []), indent=2)}
----------------------------------------

Perform a transaction risk investigation and provide a comprehensive report following these guidelines:
1. What was examined: Describe the customer profile, volume of transactions, dates covered, and total debits/credits.
2. Risk assessment against rules: Evaluate whether any activity triggers any of the bank's risk rules. For each finding, explain the specifics and cite the exact rule ID (e.g. RULE-01, RULE-04).
3. Overall summary and risk rating: Assign an overall risk rating (LOW, MEDIUM, or HIGH) based strictly on what the data shows against the rules.
4. Crucial rule: Never state that fraud occurred or accuse the customer. Only report what the data shows against the established rules.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        report_text = response.text
        return {
            "success": True,
            "customer_id": customer_data.get("customer_id"),
            "customer_name": customer_data.get("customer_name"),
            "report": report_text,
            "model": "gemini-2.5-flash-lite"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"LLM investigation failed: {str(e)}"
        }


@app.get("/api/rules")
def get_rules():
    return {"rules": load_rules()}


@app.get("/api/customers")
def get_customers():
    return {"customers": load_sample_customers()}


@app.post("/api/investigate")
async def investigate_customer(payload: Dict[str, Any]):
    try:
        customer_id = payload.get("customer_id")
        customer_data = payload.get("customer_data")

        if not customer_data and customer_id:
            samples = load_sample_customers()
            customer_data = samples.get(customer_id)

        if not customer_data:
            return JSONResponse({"success": False, "error": "Customer transaction history not found or provided."}, status_code=400)

        result = run_investigation(customer_data)
        if not result.get("success"):
            return JSONResponse(result, status_code=400)
        return result
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
