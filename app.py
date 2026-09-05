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
            "error": "GEMINI_API_KEY environment variable is not set. Please export GEMINI_API_KEY before running investigations."
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
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
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
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand h1 { font-size: 1.35rem; font-weight: 700; color: #fff; letter-spacing: -0.02em; }
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
    @media (max-width: 1024px) {
      main { grid-template-columns: 1fr; }
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
      max-height: 220px;
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
      max-height: 150px;
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
      line-height: 1.6;
      color: #e2e8f0;
      min-height: 400px;
    }
    .report-output h2, .report-output h3 {
      color: #93c5fd;
      margin: 1rem 0 0.5rem 0;
      font-size: 1.05rem;
    }
    .report-output h2:first-child, .report-output h3:first-child { margin-top: 0; }
    .report-output ul { margin-left: 1.25rem; margin-bottom: 0.75rem; }
    .report-output li { margin-bottom: 0.35rem; }
    .report-output p { margin-bottom: 0.75rem; }
    .rule-cite {
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.4);
      padding: 0.1rem 0.35rem;
      border-radius: 4px;
      font-family: monospace;
      font-weight: 600;
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
    .alert-box {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid var(--danger);
      color: #fca5a5;
      padding: 0.85rem 1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      display: none;
      line-height: 1.4;
    }
    .spinner {
      width: 18px;
      height: 18px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      display: none;
    }
    #customJsonBox {
      display: none;
      width: 100%;
      height: 140px;
      background: #0f172a;
      color: #38bdf8;
      border: 1px solid var(--panel-border);
      padding: 0.5rem;
      font-family: monospace;
      font-size: 0.8rem;
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
        <select id="customerSelect"></select>
      </div>

      <div class="customer-meta" id="customerMeta">
        <div><span>Customer ID</span><strong id="metaId">-</strong></div>
        <div><span>Account Name</span><strong id="metaName">-</strong></div>
        <div><span>Account Type</span><strong id="metaType">-</strong></div>
        <div><span>KYC Status</span><strong id="metaKyc">-</strong></div>
      </div>

      <textarea id="customJsonBox" placeholder="Paste custom customer transaction JSON here..."></textarea>

      <div id="tableSection">
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
        <span style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.35rem; display: block;">Bank Risk Rules Policy (Full Prompt Context Injection):</span>
        <div class="rules-box" id="rulesBox">Loading bank risk rules...</div>
      </div>
    </section>

    <section class="card">
      <div class="card-title">
        <span>Investigation Report</span>
        <span id="reportStatus" style="font-size: 0.75rem; color: var(--text-muted);">Awaiting assessment</span>
      </div>

      <div id="errorAlert" class="alert-box"></div>

      <div id="reportContainer" class="report-output">
        <div class="empty-state" id="emptyState">
          <p><strong>No investigation report generated yet.</strong></p>
          <p style="font-size: 0.8rem;">Select a customer and click <strong>"Run Risk Assessment"</strong> to produce an objective investigation report.</p>
        </div>
      </div>
    </section>
  </main>

  <script>
    let customersData = {};

    function formatMarkdown(text) {
      if (!text) return '';
      // Escape basic html
      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Headers
      html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
      html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
      html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');

      // Bold
      html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');

      // Rule citations highlighting
      html = html.replace(/(\\[?(RULE-\\d+)\\]?)/g, '<span class="rule-cite">$1</span>');

      // Line breaks and list formatting
      const lines = html.split('\\n');
      let inList = false;
      let out = '';
      for (let line of lines) {
        line = line.trim();
        if (line.startsWith('- ') || line.startsWith('* ')) {
          if (!inList) { out += '<ul>'; inList = true; }
          out += `<li>${line.substring(2)}</li>`;
        } else if (/^\\d+\\.\\s/.test(line)) {
          if (!inList) { out += '<ul>'; inList = true; }
          out += `<li>${line.replace(/^\\d+\\.\\s/, '')}</li>`;
        } else {
          if (inList) { out += '</ul>'; inList = false; }
          if (line.startsWith('<h2>') || line.startsWith('<h3>')) {
            out += line;
          } else if (line.length > 0) {
            out += `<p>${line}</p>`;
          }
        }
      }
      if (inList) out += '</ul>';
      return out;
    }

    async function init() {
      try {
        const [rulesRes, custRes] = await Promise.all([
          fetch('/api/rules'),
          fetch('/api/customers')
        ]);
        const rulesJson = await rulesRes.json();
        const custJson = await custRes.json();

        document.getElementById('rulesBox').textContent = rulesJson.rules || 'No rules found';
        customersData = custJson.customers || {};

        const select = document.getElementById('customerSelect');
        select.innerHTML = '';
        for (const [id, cust] of Object.entries(customersData)) {
          const opt = document.createElement('option');
          opt.value = id;
          opt.textContent = `${cust.customer_id} - ${cust.customer_name} (${cust.account_type})`;
          select.appendChild(opt);
        }

        const customOpt = document.createElement('option');
        customOpt.value = '__custom__';
        customOpt.textContent = 'Custom JSON Input...';
        select.appendChild(customOpt);

        if (Object.keys(customersData).length > 0) {
          selectCustomer(Object.keys(customersData)[0]);
        }
      } catch (err) {
        console.error('Initialization error:', err);
      }
    }

    function selectCustomer(id) {
      const customBox = document.getElementById('customJsonBox');
      const tableSec = document.getElementById('tableSection');

      if (id === '__custom__') {
        customBox.style.display = 'block';
        tableSec.style.display = 'none';
        document.getElementById('metaId').textContent = 'CUSTOM';
        document.getElementById('metaName').textContent = 'Custom Input';
        document.getElementById('metaType').textContent = 'Custom';
        document.getElementById('metaKyc').textContent = 'Unspecified';
        if (!customBox.value) {
          customBox.value = JSON.stringify({
            customer_id: "CUST-CUSTOM",
            customer_name: "Jane Doe",
            account_type: "Checking",
            kyc_tier: "Tier 1",
            transactions: [
              {
                txn_id: "TXN-001",
                date: "2026-09-01T12:00:00",
                type: "CREDIT",
                amount: 1000.0,
                description: "Payroll",
                mcc: null,
                location: "US"
              }
            ]
          }, null, 2);
        }
        return;
      }

      customBox.style.display = 'none';
      tableSec.style.display = 'block';

      const cust = customersData[id];
      if (!cust) return;

      document.getElementById('metaId').textContent = cust.customer_id;
      document.getElementById('metaName').textContent = cust.customer_name;
      document.getElementById('metaType').textContent = cust.account_type;
      document.getElementById('metaKyc').textContent = cust.kyc_tier;

      const tbody = document.querySelector('#txnTable tbody');
      tbody.innerHTML = '';
      (cust.transactions || []).forEach(txn => {
        const tr = document.createElement('tr');
        const formattedAmount = (txn.type === 'CREDIT' ? '+' : '-') + '$' + Number(txn.amount).toLocaleString(undefined, {minimumFractionDigits: 2});
        tr.innerHTML = `
          <td>${txn.date ? txn.date.replace('T', ' ') : ''}</td>
          <td class="${txn.type === 'CREDIT' ? 'type-credit' : 'type-debit'}">${txn.type}</td>
          <td>${formattedAmount}</td>
          <td>${txn.description || ''}</td>
          <td>${txn.mcc || '-'}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    document.getElementById('customerSelect').addEventListener('change', (e) => {
      selectCustomer(e.target.value);
    });

    document.getElementById('runBtn').addEventListener('click', async () => {
      const selectedId = document.getElementById('customerSelect').value;
      const btn = document.getElementById('runBtn');
      const btnText = document.getElementById('btnText');
      const spinner = document.getElementById('btnSpinner');
      const errorAlert = document.getElementById('errorAlert');
      const reportContainer = document.getElementById('reportContainer');
      const reportStatus = document.getElementById('reportStatus');

      errorAlert.style.display = 'none';
      btn.disabled = true;
      btnText.textContent = 'Analyzing with Gemini...';
      spinner.style.display = 'inline-block';
      reportStatus.textContent = 'Running assessment...';

      let payload = {};
      if (selectedId === '__custom__') {
        try {
          payload = { customer_data: JSON.parse(document.getElementById('customJsonBox').value) };
        } catch (jsonErr) {
          errorAlert.textContent = 'Invalid JSON in Custom Input: ' + jsonErr.message;
          errorAlert.style.display = 'block';
          btn.disabled = false;
          btnText.textContent = 'Run Risk Assessment';
          spinner.style.display = 'none';
          reportStatus.textContent = 'Invalid Input';
          return;
        }
      } else {
        payload = { customer_id: selectedId };
      }

      try {
        const res = await fetch('/api/investigate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
          throw new Error(data.error || 'Investigation failed');
        }

        reportContainer.innerHTML = formatMarkdown(data.report);
        reportStatus.textContent = 'Assessment complete (gemini-2.5-flash-lite)';
      } catch (err) {
        errorAlert.textContent = err.message;
        errorAlert.style.display = 'block';
        reportStatus.textContent = 'Assessment failed';
      } finally {
        btn.disabled = false;
        btnText.textContent = 'Run Risk Assessment';
        spinner.style.display = 'none';
      }
    });

    init();
  </script>
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
