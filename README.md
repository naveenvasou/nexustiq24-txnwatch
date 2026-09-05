Track: 6

# TxnWatch - Banking Transaction Risk Investigation

TxnWatch is an AI-assisted transaction risk investigation tool designed for bank compliance teams and financial crime investigators. When an investigator is assigned a customer's transaction history, they must determine whether anything in the record warrants closer scrutiny against bank compliance policies.

TxnWatch automates this initial triage: it inspects transaction logs against defined bank risk rules, produces a structured investigation report citing the relevant rule IDs, and assigns an objective risk rating. In accordance with banking standards, the system never asserts that fraud occurred—it objectively reports what the data demonstrates against the rules.

## What the Project Does

- **Automated Risk Assessment**: Evaluates customer debits, credits, velocity, counterparty MCCs, and amounts against the bank's transaction monitoring policy.
- **Rule-by-Rule Citations**: Flags suspicious transactions and cites the specific rule ID (e.g. `[RULE-01]`, `[RULE-04]`).
- **Objective Findings**: Focuses on evidence without declaring guilt or assuming fraudulent intent.
- **Interactive Investigator Dashboard**: A single-page web UI allows investigators to select customer profiles or input custom transaction logs, review the ledger, and inspect generated reports in real-time.

## How to Run

### 1. Set the API Key
TxnWatch utilizes Google's `gemini-2.5-flash-lite` model. Ensure your `GEMINI_API_KEY` is exported:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
python app.py
```

The application will start both backend and frontend together at:
**http://localhost:8000**

You can also test the endpoint directly:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/
```

## Generated Data and Documents

To validate the investigation workflow, realistic mock banking data and compliance policies were generated and included in the repository:

- `data/risk_rules.txt`: Bank risk monitoring policy containing 5 core compliance rules:
  - **RULE-01 (Rapid High-Value Outflows)**: Outbound transfers exceeding $10,000 within 24 hours.
  - **RULE-02 (Structuring / Smurfing Pattern)**: Repeated deposits or transfers between $9,000 and $9,999.
  - **RULE-03 (Sudden Geographic Velocity Anomaly)**: Consecutive transactions in geographically distant jurisdictions in an impossible timeframe.
  - **RULE-04 (High-Risk Merchant Category Activity)**: Abnormal transaction spikes to cryptocurrency exchanges (MCC 6051), remitters (MCC 4829), or gambling.
  - **RULE-05 (Rapid Account Drainage Post-Inflow)**: Disbursing >80% of balance within 48 hours of large credit inflows.
- `data/customer_101.json`: Marcus Vance (Personal Checking). Contains regular payroll and grocery activity followed by a $12,000 inflow and rapid outbound wires to crypto exchange and remittance services, triggering RULE-01 and RULE-04.
- `data/customer_102.json`: Elena Rostova (Everyday Checking). Contains routine household spending (groceries, coffee, utility bill, streaming subscription, small ATM withdrawal) representing a clean profile.

## Technical Architecture & Implementation Notes

- **Model**: `gemini-2.5-flash-lite` via `google-genai`.
- **Context Injection**: Built as a rapid hackathon prototype, the system injects the full bank risk policy directly into the prompt context for each investigation rather than maintaining a vector database or embedding index.
- **Single-File Delivery**: The entire server, API routes, and investigator frontend UI are packaged within `app.py` for zero-setup execution.
- **Requirements**: Kept minimal with `fastapi`, `uvicorn`, `google-genai`, and `pydantic`.

## Demo Video

Walkthrough video demonstration: [https://youtu.be/k9fB5rQ3X8c](https://youtu.be/k9fB5rQ3X8c)
