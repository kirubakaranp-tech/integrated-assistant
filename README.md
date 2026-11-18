# Integrated AI Assistant

A FastAPI backend for an AI assistant that answers questions about your documents (RAG).

- **Part 1:** upload a PDF or Word file. The app reads the text, splits it into chunks,
  creates embeddings and saves everything in Chroma.
- **Part 2:** ask questions with `POST /chat`. The app finds the matching chunks, asks OpenAI
  (gpt-4o-mini) to answer from them, and returns the answer with its sources (file and page).
  It remembers the last 5 messages of each session, so follow-up questions work.

## Setup

You need Python 3.10 or newer and an OpenAI API key (https://platform.openai.com/api-keys).

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and put your key after `OPENAI_API_KEY=`. The `.env` file is in `.gitignore`,
so your key is never committed.

(On Mac/Linux activate with `source .venv/bin/activate`.)

To use another model, change `OPENAI_MODEL` in `.env`.

## Run

```
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try the API in the browser.

The first upload is slower because the embedding model (about 80 MB) is downloaded once.

## Endpoints

- `POST /documents` - upload a `.pdf` or `.docx` file (form field `file`)
- `GET /documents` - list the uploaded documents
- `POST /chat` - ask a question about the documents
- `GET /health` - check that the server is running

### Upload

```
curl.exe -F "file=@samples/policy.pdf" http://127.0.0.1:8000/documents
{"id":"d1","chunks":7}
```

Errors: 415 for files that aren't PDF or Word, 400 for an empty file, 413 for a file over
20 MB, 422 when no text can be read (for example a scanned PDF) and 503 when the embedding
model can't be loaded.

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
  "session_id": "user-1"
}
```

A follow-up in the same session, like `{"message": "And earned leave?", "session_id": "user-1"}`,
is understood because the app keeps the last 5 messages of the session.
If nothing in the documents matches the question, the answer is `"I don't know"` with no sources.
Word files have no pages, so their sources have `"page": null`.

## How it works

Upload:

1. Check the file type: the extension and the first bytes of the file
2. Read the text: PyMuPDF for PDF (page by page), python-docx for Word (tables too)
3. Split the text into chunks of about 800 characters, with about 120 characters of overlap
4. Create the embeddings with all-MiniLM-L6-v2 (runs locally, no API key)
5. Save the chunks in Chroma (`data/chroma`) with the file name and page in the metadata

Chat:

1. Embed the question (together with the previous question, so follow-ups find the right text)
2. Get the 4 closest chunks from Chroma and drop the ones that are too far away
3. If no chunk is left, answer "I don't know" without calling the model
4. Otherwise send the model: the rules, the session history, the chunks and the question
5. Save the question and answer in the session memory

The settings (chunk size, number of chunks, distance limit, memory size) are in `app/config.py`.
If good questions get "I don't know", raise `MAX_DISTANCE` a little; if unrelated questions
get answers, lower it.

## Project structure

```
app/
  main.py               FastAPI app
  config.py             settings
  api/
    documents.py        the /documents endpoints
    chat.py             the /chat endpoint
  schemas/              request and response models
  services/
    extractors.py       read text from PDF and Word files
    chunking.py         split text into chunks
    embeddings.py       create embeddings
    vector_store.py     save to Chroma, list documents, search
    memory.py           last 5 messages of each session
    prompt.py           the prompt for the model
    llm.py              call OpenAI
samples/                files to try the API with
tests/
```

## Tests

```
pytest
```

The tests use a temporary database, fake embeddings and a fake LLM, so they run without
internet and without an API key.
