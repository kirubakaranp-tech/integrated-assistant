# Scenario results

Run: 2026-11-19 16:18 | Model: `openai/gpt-oss-120b` | Passed: 10/10

| # | Type | Question | Result | Time | Tools used | Answer | Problems |
|---|---|---|---|---|---|---|---|
| D1 | Document | How many days of earned leave do full-time employees get? | PASS | 1.0s | - | Full‑time employees receive **18 days of earned leave** each year. | - |
| D2 | Document | How many days a week can head-office staff work remotely? | PASS | 1.8s | - | Head‑office staff can work remotely for up to **two days a week**. | - |
| D3 | Document | How long must a password be? | PASS | 2.2s | - | Passwords must be at least 14 characters long. | - |
| U1 | Unanswerable | What is the capital of France? | PASS | 1.1s | - | I don't know | - |
| U2 | Unanswerable | What is the company dress code? | PASS | 2.3s | - | I don't know | - |
| C1 | CRM | Which plan is customer 3 on? | PASS | 2.3s | get_customer_details(3) | Customer 3 (Rahul) is on the Standard plan. | - |
| C2 | CRM | What is the email address of customer 9? | PASS | 1.5s | get_customer_details(9) | There is no customer with id 9. | - |
| O1 | Order | Where is order 1042? | PASS | 1.2s | get_order_status(1042) | Order 1042 (customer 3) is currently **out for delivery**. It was s... | - |
| O2 | Order | Show me all orders of customer 3. | PASS | 2.1s | get_customer_orders(3) | Customer 3’s orders: - Order 1047 – processing – 15 Mar 2026 – ₹4,9... | - |
| E1 | Email draft | Which plan is customer 3 on? | PASS | 3.4s | get_customer_details(3) | Subject: Your Plan Information | - |
