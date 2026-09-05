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
            "error": "GEMINI_API_KEY environment variable is not set. Please set GEMINI_API_KEY to run live investigations."
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


HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TxnWatch - Transaction Risk Investigation</title>
  <style>
    :root {
      --bg: #0f172a;
      --panel: #1e293b;
      --panel-border: #334155;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --danger: #ef4444;
      --warning: #f59e0b;
      --success: #10b981;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: var(--panel);
      border-bottom: 1px solid var(--panel-border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand h1 { font-size: 1.35rem; font-weight: 700; color: #fff; }
    .brand span { font-size: 0.85rem; color: var(--text-muted); }
    .badges { display: flex; gap: 0.5rem; align-items: center; }
    .badge {
      font-size: 0.75rem;
      padding: 0.25rem 0.6rem;
      border-radius: 9999px;
      font-weight: 600;
      background: #334155;
      color: #cbd5e1;
    }
    .badge.track { background: #1e3a8a; color: #93c5fd; }
    .badge.model { background: #064e3b; color: #6ee7b7; }
    main {
      flex: 1;
      padding: 1.5rem 2rem;
      display: grid;
      grid-template-columns: 1fr 1.15fr;
      gap: 1.5rem;
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .card-title {
      font-size: 1.05rem;
      font-weight: 600;
      color: #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--panel-border);
      padding-bottom: 0.5rem;
    }
    select, button, textarea {
      font-family: inherit;
      border-radius: 6px;
      font-size: 0.9rem;
    }
    select {
      width: 100%;
      background: #0f172a;
      color: var(--text);
      border: 1px solid var(--panel-border);
      padding: 0.6rem 0.75rem;
      cursor: pointer;
    }
    .customer-meta {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
      background: #0f172a;
      padding: 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
    }
    .customer-meta div span { color: var(--text-muted); display: block; font-size: 0.75rem; }
    .customer-meta div strong { color: #f1f5f9; }
    .table-container {
      overflow-x: auto;
      max-height: 250px;
      overflow-y: auto;
      border: 1px solid var(--panel-border);
      border-radius: 6px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
    }
    th, td {
      padding: 0.5rem 0.6rem;
      text-align: left;
      border-bottom: 1px solid var(--panel-border);
    }
    th { background: #0f172a; color: var(--text-muted); font-weight: 600; position: sticky; top: 0; }
    tr:hover td { background: #243248; }
    .type-credit { color: var(--success); font-weight: 600; }
    .type-debit { color: #f87171; font-weight: 600; }
    .btn-action {
      background: var(--accent);
      color: white;
      border: none;
      padding: 0.75rem 1.25rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: background 0.2s;
    }
    .btn-action:hover { background: var(--accent-hover); }
    .btn-action:disabled { opacity: 0.6; cursor: not-allowed; }
    .rules-box {
      font-size: 0.8rem;
      background: #0f172a;
      border: 1px solid var(--panel-border);
      border-radius: 6px;
      padding: 0.75rem;
      max-height: 160px;
      overflow-y: auto;
      color: #94a3b8;
      white-space: pre-wrap;
    }
    .report-output {
      flex: 1;
      background: #0f172a;
      border: 1px solid var(--panel-border);
      border-radius: 6px;
      padding: 1.25rem;
      overflow-y: auto;
      font-size: 0.9rem;
      white-space: pre-wrap;
      line-height: 1.6;
      color: #e2e8f0;
      min-height: 380px;
    }
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      min-height: 340px;
      color: var(--text-muted);
      text-align: center;
      gap: 0.75rem;
    }
    .spinner {
      width: 24px;
      height: 24px;
      border: 3px solid rgba(255,255,255,0.2);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      display: none;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1>TxnWatch</h1>
      <span>Banking Transaction Risk Investigation Dashboard</span>
    </div>
    <div class="badges">
      <span class="badge track">Track 6: Banking</span>
      <span class="badge model">gemini-2.5-flash-lite</span>
    </div>
  </header>

  <main>
    <section class="card">
      <div class="card-title">
        <span>Customer & Transaction History</span>
      </div>

      <div>
        <label style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.35rem; display: block;">Select Customer Profile:</label>
        <select id="customerSelect">
          <option value="CUST-84920">CUST-84920 - Marcus Vance (Flagged Outflows & Crypto MCC)</option>
          <option value="CUST-19342">CUST-19342 - Elena Rostova (Routine Household Transactions)</option>
        </select>
      </div>

      <div class="customer-meta" id="customerMeta">
        <div><span>Customer ID</span><strong id="metaId">-</strong></div>
        <div><span>Account Name</span><strong id="metaName">-</strong></div>
        <div><span>Account Type</span><strong id="metaType">-</strong></div>
        <div><span>KYC Status</span><strong id="metaKyc">-</strong></div>
      </div>

      <div>
        <span style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.35rem; display: block;">Transaction Logs Under Review:</span>
        <div class="table-container">
          <table id="txnTable">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Description</th>
                <th>MCC</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <button id="runBtn" class="btn-action">
        <span id="btnText">Run Risk Assessment</span>
        <div id="btnSpinner" class="spinner"></div>
      </button>

      <div>
        <span style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.35rem; display: block;">Bank Risk Rules Policy (Direct Context Injection):</span>
        <div class="rules-box" id="rulesBox">Loading bank risk rules...</div>
      </div>
    </section>

    <section class="card">
      <div class="card-title">
        <span>Investigation Report</span>
        <span id="reportStatus" style="font-size: 0.75rem; color: var(--text-muted);">Awaiting assessment</span>
      </div>

      <div id="reportContainer" class="report-output">
        <div class="empty-state" id="emptyState">
          <p>No investigation report generated yet.</p>
          <p style="font-size: 0.8rem;">Select a customer and click <strong>"Run Risk Assessment"</strong> to produce an objective investigation report.</p>
        </div>
      </div>
    </section>
  </main>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_UI


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
