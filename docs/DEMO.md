# 5-minute demo

Shows document Q&A, a tool call, a refusal and the email draft on the chat page.

## Before the demo (10 minutes earlier)

1. Start the three terminals from the README: CRM, API and chat page.
2. Open http://localhost:5500 and upload `samples/policy.pdf` and `samples/handbook.docx`,
   so the embedding model is already downloaded.
3. Ask one question to check that the LLM key works, then click **New chat**.
4. Open `docs/architecture.png` in a second tab.
5. Zoom the browser to 125% so everyone can read it.
6. Keep the screenshots in `output/` ready as a backup in case the internet or the LLM fails.

On the free Groq plan, wait a few seconds between questions so you don't hit the per-minute limit.

## The demo

| Time | Show | Say |
|---|---|---|
| 0:00 - 0:40 | The architecture diagram | "One FastAPI backend. Documents go into Chroma. Customer data comes from a CRM API and orders from PostgreSQL. The LLM decides which one to use." |
| 0:40 - 1:40 | **Document Q&A.** Ask *How many days of earned leave do full-time employees get?*, then *And how many days of sick leave?* | "18 days, and the source is policy.pdf page 1. The second question is a follow-up: it remembers the last 5 messages." |
| 1:40 - 2:40 | **Tool call.** Click **New chat**. Ask *Which plan is customer 3 on?*, then *Where is order 1042?* Open **How I got this** under each answer | "Here it called `get_customer_details(3)` on the CRM, and here `get_order_status(1042)` on PostgreSQL. The LLM only picks the tool and the id. It never writes SQL, and the database user is read-only." |
| 2:40 - 3:40 | **Email draft.** Keep the same chat. Choose **Formal**, click **Draft email**. Then choose **Friendly** and click it again | "It turns this conversation into an email with a subject and body. It is checked by Pydantic and it is never sent. Staff copy it and review it first." |
| 3:40 - 4:20 | **Refusal.** Click **New chat**. Ask *What is the capital of France?*, then *What is the company dress code?* | "When the answer is not in the documents or the tools, it says I don't know instead of guessing." |
| 4:20 - 5:00 | The terminal: run `python -m pytest`, then show `output/scenario_results.md` | "88 unit tests, the CRM and order tools are tested with mocks, and 10 end-to-end scenarios are recorded with time and tools. No keys are in the code: `.env` is ignored and checked by `scripts/check_secrets.py`." |

## If someone asks

- **Why can't it change an order?** There is no write tool, and the database user only has `SELECT`.
- **What if the CRM is down?** The tool retries server errors 3 times, has a 5 second timeout and
  then tells the user the CRM is not reachable, instead of crashing.
- **Which model?** Any OpenAI-compatible API. Set `OPENAI_BASE_URL` and `OPENAI_MODEL` in `.env`.
