# Test report

Date: 19 November 2026 · Branch: `feature/assistant` · Model: `openai/gpt-oss-120b` (Groq)

## Summary

| Check | Result |
|---|---|
| End-to-end scenarios, first run | 7 of 10 passed |
| End-to-end scenarios, after fixes | **10 of 10 passed** |
| Unit tests (`python -m pytest`) | 88 passed (81 passed and 7 skipped without PostgreSQL) |
| Mocked tool tests (`tests/test_tool_mocks.py`) | 15 passed |
| Secrets check (`scripts/check_secrets.py`) | No keys in the code or history. One old database password in history, now removed from the code (see below) |

## How the scenarios were run

`python scripts/run_scenarios.py` sends 10 questions to the running API (with the real CRM, the
real PostgreSQL database, the real embedding model and the real LLM). Every scenario uses a new
session. It checks the answer text, the tool that was used and the source file, measures the
response time, and saves the table to `output/scenario_results.md`.

| Kind | Count | Pass rule |
|---|---|---|
| Document questions | 3 | Right fact in the answer and the right source file |
| Unanswerable questions | 2 | Answer is exactly "I don't know" |
| CRM questions | 2 | Right tool, right data, and a clean message for an unknown customer |
| Order questions | 2 | Right tool and right status or order ids |
| Email draft | 1 | `/draft-email` returns a subject and a body that starts with "Dear" and names the customer |

## Scenario results after the fixes

| # | Type | Question | Result | Time | Tools used | Answer |
|---|---|---|---|---|---|---|
| D1 | Document | How many days of earned leave do full-time employees get? | PASS | 1.0s | - | Full-time employees receive 18 days of earned leave each year. |
| D2 | Document | How many days a week can head-office staff work remotely? | PASS | 1.8s | - | Head-office staff can work remotely for up to two days a week. |
| D3 | Document | How long must a password be? | PASS | 2.2s | - | Passwords must be at least 14 characters long. |
| U1 | Unanswerable | What is the capital of France? | PASS | 1.1s | - | I don't know |
| U2 | Unanswerable | What is the company dress code? | PASS | 2.3s | - | I don't know |
| C1 | CRM | Which plan is customer 3 on? | PASS | 2.3s | get_customer_details(3) | Customer 3 (Rahul) is on the Standard plan. |
| C2 | CRM | What is the email address of customer 9? | PASS | 1.5s | get_customer_details(9) | There is no customer with id 9. |
| O1 | Order | Where is order 1042? | PASS | 1.2s | get_order_status(1042) | Order 1042 (customer 3) is currently out for delivery. It was shipped... |
| O2 | Order | Show me all orders of customer 3. | PASS | 2.1s | get_customer_orders(3) | Customer 3's orders: Order 1047 - processing - 15 Mar 2026 - ₹4,999... |
| E1 | Email draft | Which plan is customer 3 on? | PASS | 3.4s | get_customer_details(3) | Subject: Your Plan Information |

Average response time: 1.9 seconds. The first run is kept in
[scenario_results_run1.md](scenario_results_run1.md).

## Failures found and fixed

| # | Found by | Problem | Fix | Result |
|---|---|---|---|---|
| 1 | Secrets check | The read-only database password was written in `app/config.py` and `database/readonly_user.sql` | The password now lives only in `.env` (`DATABASE_URL`). `database/setup.py` creates or updates the user with it, so running setup again also changes an old password | Files in the repo: OK |
| 2 | Scenario C1 and E1 | The answer said "Customer 3 is on the Standard plan" without the name, so the email draft had no name either | The prompt now asks for the customer's name and key dates from the tool result, and says never to guess a name | C1 and E1 pass |
| 3 | Scenario C2 | The CRM said "There is no customer with id 9", but the model replied "I don't know" | The prompt now tells the model to pass on a tool's "does not exist" or "not reachable" message | C2 passes |
| 4 | Scenario O2 (passed, but wrong) | Amounts were shown in dollars | The prompt now says all amounts are Indian rupees (₹) | O2 shows ₹ |
| 5 | Dry run of the script | `run_scenarios.py` crashed with a long error when the API was not running | It now prints "Cannot reach the API ... Start it first" | Clear message |

## Unit tests for the tools (mocked)

`tests/test_tool_mocks.py` tests the tools without a running CRM or database:

- **CRM tool** (`requests` replaced by a fake): customer found, 404, other error status (500),
  connect timeout, read timeout, server errors after retries, CRM down. It also checks the URL and timeout.
- **Order tools** (`psycopg` connection replaced by a fake): order with items, unknown order,
  customer orders, customer without orders, database down, permission error, connection failure.
  It also checks that the id is passed as a query parameter and never put inside the SQL text.

The real-database tests in `tests/test_order_tools.py` also check that the read-only user cannot
`DELETE`, `UPDATE` or `DROP`.

## Secrets hygiene

`python scripts/check_secrets.py` looks for OpenAI, Groq, GitHub and Google keys and for passwords
in database URLs and SQL, in every file in the repo and in the whole git history.

- `.env` is in `.gitignore` and was never committed.
- No API key appears in the code or in any commit.
- The old read-only password is still in commit `f35b0fb`, because history cannot change without
  rewriting it. It is a local, read-only database user. The fix is to set a new password in `.env`
  and run `python -m database.setup`, which makes the old one useless.
- `.env.example` only has placeholders (`sk-your-key-here`, `CHOOSE_A_PASSWORD`).

## Limits

- The LLM is not fully predictable, so a run can differ slightly. The checks look for key facts, not exact wording.
- The free Groq plan has a per-minute limit, so the script waits 15 seconds between scenarios.
- The response times are from one run on a local PC.
