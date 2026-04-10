# ERPNext Tally Sync — `erpnext_tally_sync`

Real-time, bi-directional accounting sync between **ERPNext** and **Tally Prime**.  
Syncs Sales Invoices, Purchase Invoices, Payment Entries, Receipt Entries, and Journal Entries as Tally vouchers via Tally's built-in XML/TDL gateway on port 9000.

---

## Supported Document Types

| ERPNext DocType     | Tally Voucher Type          |
|---------------------|-----------------------------|
| Sales Invoice       | Sales                       |
| Purchase Invoice    | Purchase                    |
| Payment Entry (Pay) | Payment                     |
| Payment Entry (Receive) | Receipt                 |
| Payment Entry (Internal Transfer) | Contra        |
| Journal Entry       | Journal                     |

---

## Prerequisites

- ERPNext v14 or v15
- Python 3.10+
- Tally Prime 2.x or 3.x (with Gateway Server enabled)
- Network connectivity from ERPNext server to Tally machine on port 9000

---

## Step 1 — Enable Tally Prime Gateway

1. Open Tally Prime → Press **F12** → **Advanced Configuration**
2. Set **"Enable Tally Gateway Server"** → **Yes**
3. Set **Port** → `9000` (default)
4. Set **"Allow TDML Import"** → **Yes**
5. Ensure the correct company is open in Tally

Test connectivity from your ERPNext server:
```bash
curl -X POST http://<TALLY_IP>:9000 \
  -H "Content-Type: text/xml" \
  -d '<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE><ID>List of Companies</ID></HEADER></ENVELOPE>'
```
You should see an XML response listing your Tally companies.

---

## Step 2 — Install the App

```bash
# On your Frappe bench directory
cd /home/frappe/frappe-bench

# Get the app (from local path or GitHub)
bench get-app erpnext_tally_sync /path/to/erpnext_tally_sync
# OR from GitHub once published:
# bench get-app erpnext_tally_sync https://github.com/your-org/erpnext_tally_sync

# Install on your site
bench --site your-site.com install-app erpnext_tally_sync

# Run migrations (creates the 3 new DocTypes)
bench --site your-site.com migrate

# Restart
bench restart
```

---

## Step 3 — Configure Tally Settings

1. In ERPNext, go to **Tally Sync → Tally Settings**
2. Fill in:
   - **Tally Host / IP** — IP of the Windows machine running Tally Prime
   - **Tally Port** — `9000`
   - **Tally Company Name** — Must match exactly what is open in Tally (case-sensitive)
   - **Enable Tally Sync** — ✅ Checked
   - **Sync Immediately on Submit** — ✅ Checked (or uncheck to use scheduled sync)
   - **Request Timeout** — `30` seconds (increase if Tally is slow)
   - **XML Encoding** — `utf-16` (default, required by Tally Prime)
   - **Company GSTIN** — Your 15-character GSTIN

3. Click **Test Connection** (via API call below) to verify before going live.

---

## Step 4 — Set Up Ledger Mappings

ERPNext account names differ from Tally ledger names. Map them in:
**Tally Sync → Tally Ledger Mapping**

### Common mappings to configure:

| ERPNext Account (example)            | Tally Ledger Name         |
|--------------------------------------|---------------------------|
| Debtors - COMP                       | Sundry Debtors            |
| Creditors - COMP                     | Sundry Creditors          |
| Cash - COMP                          | Cash                      |
| Bank Account - COMP                  | HDFC Bank                 |
| Output Tax CGST - COMP               | Output CGST               |
| Output Tax SGST - COMP               | Output SGST               |
| Output Tax IGST - COMP               | Output IGST               |
| Input Tax Credit CGST - COMP         | Input CGST                |
| Input Tax Credit SGST - COMP         | Input SGST                |
| Sales - COMP                         | Sales Account             |
| Cost of Goods Sold - COMP            | Purchase Account          |

> **Tip:** If no mapping exists for an account, the system falls back to the ERPNext account name. Add mappings only where names differ.

---

## Step 5 — Verify Auto-Sync

1. Submit a **Sales Invoice** in ERPNext
2. Check the green/orange alert banner — it will confirm sync status
3. Go to **Tally Sync → Tally Sync Log** to see the detailed log
4. Open Tally Prime → **Day Book** → verify the voucher appeared

---

## REST API Endpoints

All endpoints require System Manager role.

### Test Connection
```
GET /api/method/erpnext_tally_sync.api.test_connection
```

### Manual Sync (retry a single document)
```
POST /api/method/erpnext_tally_sync.api.manual_sync
Content-Type: application/json

{
  "doctype": "Sales Invoice",
  "docname": "SINV-2024-00001"
}
```

### Bulk / Backfill Sync (date range)
```
POST /api/method/erpnext_tally_sync.api.bulk_sync
Content-Type: application/json

{
  "doctype": "Sales Invoice",
  "from_date": "2024-04-01",
  "to_date": "2024-03-31"
}
```

### Get Sync Status for a Document
```
GET /api/method/erpnext_tally_sync.api.get_sync_status
  ?doctype=Sales Invoice&docname=SINV-2024-00001
```

---

## Tally Sync Log

Every sync attempt creates a **Tally Sync Log** record with:
- Reference document & DocType
- Tally voucher type & number
- Sync Status: `Pending / Success / Failed / Cancelled`
- Full XML payload sent (for debug)
- Raw Tally response
- Error message & traceback on failure
- Retry count & next scheduled retry time

---

## Automatic Retry

Failed syncs are retried automatically by a **scheduled hourly job**.
- Each retry increments the retry counter
- Next retry delay doubles each time (30 min, 60 min, 90 min…)
- Stops retrying after **Max Retries** (configured in Tally Settings, default: 3)

---

## Cancellation Behaviour

When an ERPNext document is **cancelled**:
- A `DELETE` action XML is sent to Tally to remove the voucher
- The Tally Sync Log is marked `Cancelled`
- If Tally deletion fails, a warning is shown — manual deletion in Tally may be needed

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Connection refused" on port 9000 | Enable Gateway Server in Tally F12 settings |
| `LINEERROR` in Tally response | Ledger name mismatch — check Tally Ledger Mapping |
| `STATUS=0` in Tally response | Company name mismatch in Tally Settings |
| Voucher created but wrong amounts | Check debit/credit mapping in `tally_xml.py` |
| Encoding errors | Ensure Tally Settings encoding = `utf-16` |
| Scheduled retry not firing | Run `bench restart` and check scheduler is enabled |

---

## Project Structure

```
erpnext_tally_sync/
├── setup.py
├── requirements.txt
├── MANIFEST.in
└── erpnext_tally_sync/
    ├── __init__.py
    ├── hooks.py              ← doc_events, scheduler hooks
    ├── modules.txt
    ├── patches.txt
    ├── tally_xml.py          ← all XML payload builders + HTTP transport
    ├── sync_manager.py       ← orchestration + retry scheduler
    ├── api.py                ← whitelisted REST endpoints
    └── tally_sync/
        └── doctype/
            ├── tally_settings/       ← singleton config doctype
            ├── tally_ledger_mapping/ ← account ↔ ledger name map
            └── tally_sync_log/       ← per-voucher sync audit log
```

---

## License

MIT — AVS Technologies Pvt. Ltd., Pune
