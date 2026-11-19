# Scenario results

Run: 2026-11-19 15:44 | Model: `openai/gpt-oss-120b` | Passed: 7/10

| # | Type | Question | Result | Time | Tools used | Answer | Problems |
|---|---|---|---|---|---|---|---|
| D1 | Document | How many days of earned leave do full-time employees get? | PASS | 3.2s | - | Full‑time employees receive **18 days of earned leave** each year. | - |
| D2 | Document | How many days a week can head-office staff work remotely? | PASS | 1.8s | - | Head‑office staff can work remotely for up to **two days per week**. | - |
| D3 | Document | How long must a password be? | PASS | 1.9s | - | Passwords must be at least 14 characters long. | - |
| U1 | Unanswerable | What is the capital of France? | PASS | 2.2s | - | I don't know | - |
| U2 | Unanswerable | What is the company dress code? | PASS | 1.9s | - | I don't know | - |
| C1 | CRM | Which plan is customer 3 on? | FAIL | 3.0s | get_customer_details(3) | Customer 3 is on the **Standard** plan. | missing Rahul |
| C2 | CRM | What is the email address of customer 9? | FAIL | 7.4s | get_customer_details(9) | I don't know | expected one of: no customer, not found, does not exist, doesn't ex... |
| O1 | Order | Where is order 1042? | PASS | 2.6s | get_order_status(1042) | The order is currently **out for delivery**. | - |
| O2 | Order | Show me all orders of customer 3. | PASS | 3.5s | get_customer_orders(3) | Customer 3’s orders: - Order 1047 – processing – 2026‑03‑15 – $4,99... | - |
| E1 | Email draft | Which plan is customer 3 on? | FAIL | 2.6s | get_customer_details(3) | Subject: Plan Information for Customer 3 | missing Rahul |
