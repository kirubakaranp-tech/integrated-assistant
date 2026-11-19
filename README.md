# Integrated AI Assistant

A FastAPI backend and a small chat page for an AI assistant that can:

- answer questions about uploaded PDF and Word files, with sources (RAG)
- look up customers in a CRM and orders in a PostgreSQL database (tool calling)
- turn a conversation into an email draft

Built with FastAPI, Chroma, OpenAI (gpt-4o-mini) and PostgreSQL.

## Setup

You need Python 3.10+, an [OpenAI API key](https://platform.openai.com/api-keys) and
[PostgreSQL](https://www.postgresql.org/download/).

**1. Install the packages**

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

On Mac/Linux, activate with `source .venv/bin/activate`.

**2. Add your settings**

```
copy .env.example .env
```

Open `.env` and fill in:

- `OPENAI_API_KEY` - your OpenAI key
- `DATABASE_ADMIN_URL` - replace `YOUR_POSTGRES_PASSWORD` with your postgres password

`.env` is in `.gitignore`, so your key is never committed.

**No OpenAI credit?** [Groq](https://console.groq.com) has a free plan with no credit card.
Create a key at https://console.groq.com/keys, put it in `OPENAI_API_KEY`, and set:

```
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=openai/gpt-oss-120b
```

**3. Create the orders database**

```
python -m database.setup
```

This creates `orders_db` with 20 sample orders (ids 1031 to 1050, for customers 1 to 5) and a
read-only user, `assistant_readonly`. Run it again any time to reset the data. If you change the
read-only user's password in `database/readonly_user.sql`, change `DATABASE_URL` in `.env` too.

## Run

Open three terminals in the project folder and activate `.venv` in each one.

| Terminal | Command | Then open |
|---|---|---|
| 1. Mock CRM | `uvicorn crm.main:app --port 8001` | http://127.0.0.1:8001/customers/3 |
| 2. API | `uvicorn app.main:app --reload` | http://127.0.0.1:8000/docs |
| 3. Chat page | `python -m http.server 5500 --directory frontend` | http://localhost:5500 |

The first upload is slower because the embedding model (about 80 MB) is downloaded once.

## API

| Method | Path | What it does |
|---|---|---|
| POST | `/documents` | Upload a `.pdf` or `.docx` file (form field `file`) |
| GET | `/documents` | List the uploaded documents |
| POST | `/chat` | Ask about the documents, a customer or an order |
| POST | `/draft-email` | Turn a chat session into an email draft |
| GET | `/health` | Check that the server is running |

### Upload a document

Upload `samples/policy.pdf` to `POST /documents`. Response (`201`):

```json
{"id": "d1", "chunks": 7}
```

`GET /documents` then returns:

```json
[{"id": "d1", "name": "policy.pdf"}]
```

| Status | When |
|---|---|
| 400 | The file is empty |
| 413 | The file is bigger than 20 MB |
| 415 | The file is not a PDF or Word file |
| 422 | No text can be read (for example a scanned PDF) |
| 503 | The embedding model can't be loaded (the first run needs internet) |

### Chat

Request:

```json
{"message": "How many days of sick leave do employees get?", "session_id": "user-1"}
```

Response:

```json
{
  "answer": "Employees get 10 days of sick leave each year.",
  "sources": [{"file": "policy.pdf", "page": 1}],
  "tools_used": [],
  "session_id": "user-1"
}
```

- Use the same `session_id` for follow-up questions. The last 5 messages of each session are kept.
- If nothing relevant is found, the answer is `"I don't know"`.
- Word files have no pages, so their sources have `"page": null`.

The model also decides by itself when to use a tool:

| Question | Tool | Data from |
|---|---|---|
| Which plan is customer 3 on? | `get_customer_details(3)` | Mock CRM |
| Where is order 1042? | `get_order_status(1042)` | PostgreSQL |
| Show me all orders of customer 3. | `get_customer_orders(3)` | PostgreSQL |

```
User: Where is order 1042?
Tool: get_order_status(1042)
Assistant: Order 1042 was shipped on 12 March and is out for delivery.
```

### Email draft

Request (after chatting in session `user-1`):

```json
{"session_id": "user-1", "tone": "formal"}
```

Response:

```json
{"subject": "Summary of your order query", "body": "Dear Rahul, ..."}
```

`tone` is `formal` (default) or `friendly`. The draft is only returned, never sent.

## Chat page

At http://localhost:5500 you can upload a file, chat, see the sources under each answer, open
**How I got this** to see the tools that were used, and click **Draft email** to see a draft in
the text box. It shows "Thinking..." while waiting and a friendly message when something goes wrong.

## Safety

- **Database:** the model only picks a tool and an id. It never writes SQL. Ids must be whole
  numbers, queries are parameterised (`WHERE id = %s`), and the app connects as a read-only user,
  so `DELETE`, `UPDATE` and `DROP` fail.
- **CRM:** if the CRM returns 404, is too slow (5 second timeout), has server errors (retried
  3 times) or is down, the tool gives the model a clean message instead of crashing.
- **Email:** the draft is checked with a Pydantic model, and there is no code that sends email.
- **CORS:** only the addresses in `ALLOWED_ORIGINS` (default `http://localhost:5500` and
  `http://127.0.0.1:5500`) may call the API, never `*`. Put your real frontend address there in production.

## How it works

**Upload**

1. Check the file type (the extension and the first bytes of the file)
2. Read the text: PyMuPDF for PDF, python-docx for Word
3. Split it into chunks of about 800 characters, with some overlap
4. Create embeddings with all-MiniLM-L6-v2 (runs locally, no API key)
5. Save the chunks in Chroma with the file name and page

**Chat**

1. Embed the question, together with the previous one so follow-ups work
2. Take the 4 closest chunks from Chroma
3. Send the chunks, the session history and the tools to gpt-4o-mini
4. Run any tool the model asks for and send it the result
5. Return the answer with its sources

Settings like the chunk size and `MAX_DISTANCE` (how close a chunk must be to count as relevant)
are in `app/config.py`.

## Tests

```
python -m pytest
```

The tests use fake embeddings, a fake LLM and a temporary database, so they run without internet
or an API key. The order database tests are skipped if PostgreSQL is not running.

Two scripts try the running app end to end:

| Command | What it does |
|---|---|
| `python scripts/ask_questions.py` | Asks 5 order questions |
| `python scripts/draft_emails.py` | Has 2 conversations and drafts an email for each |

## Project structure

```
app/
  main.py         FastAPI app and CORS
  config.py       settings
  api/            the endpoints: documents, chat, draft-email
  schemas/        Pydantic request and response models
  services/       text extraction, chunking, embeddings, Chroma, memory, prompt, OpenAI and tools
crm/              the mock CRM API
database/         SQL for the tables and the read-only user, and the setup script
frontend/         the chat page (HTML, CSS, JavaScript)
scripts/          the two scripts above
samples/          policy.pdf, handbook.docx and image.png to try the API with
tests/            the tests
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` when the API starts | Install into the venv: `python -m pip install -r requirements.txt` |
| `503 Could not get an answer from OpenAI` | Check `OPENAI_API_KEY` in `.env` and your OpenAI credit, then restart the API |
| `429 ... insufficient_quota` | No OpenAI credit left: add credit, or use Groq for free (see Setup step 2) |
| `429` rate limit on the free plan | Wait a minute, then ask again |
| The chat page can't reach the server | Start the API and open the page at http://localhost:5500 |
| Good questions get "I don't know" | Raise `MAX_DISTANCE` in `app/config.py` a little (lower it if unrelated questions get answers) |
