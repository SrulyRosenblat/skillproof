#!/bin/bash
# Writes a generic n8n Code (Python) node body to /workspace/code.py: it
# computes the summary from whatever item it is handed at run time (values
# are computed from the actual data, not hardcoded), so it works against
# any single-item invocation shaped like the one described in the task
# prompt.
set -euo pipefail

cat > /workspace/code.py <<'PY'
body = _json["body"]
orders = body.get("orders", [])

order_count = len(orders)
total_amount = round(sum(o["amount"] * o["quantity"] for o in orders), 2)

return [{
    "json": {
        "customer": body.get("customer"),
        "order_count": order_count,
        "total_amount": total_amount,
    }
}]
PY

echo "wrote /workspace/code.py"
