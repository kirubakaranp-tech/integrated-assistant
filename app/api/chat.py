from fastapi import APIRouter, HTTPException

from app.config import MAX_DISTANCE, TOP_K
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.embeddings import embed_texts
from app.services.llm import ask_llm
from app.services.memory import add_message, get_history
from app.services.prompt import I_DONT_KNOW, build_messages
from app.services.vector_store import search

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    history = get_history(request.session_id)

    # 1. find the chunks that match the question.
    # A follow-up like "and for sick leave?" means little alone, so we search
    # with the previous question and the new one together.
    search_text = request.message
    previous_questions = [m["content"] for m in history if m["role"] == "user"]
    if previous_questions:
        search_text = previous_questions[-1] + " " + request.message

    try:
        query_embedding = embed_texts([search_text])[0]
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not load the embedding model. The first run needs internet to download it.",
        )

    chunks = search(query_embedding, TOP_K)
    relevant_chunks = [chunk for chunk in chunks if chunk["distance"] <= MAX_DISTANCE]

    # 2. nothing relevant -> don't ask the model at all
    if not relevant_chunks:
        answer = I_DONT_KNOW
        sources = []
    else:
        # 3. ask the model, with the chunks as context
        messages = build_messages(request.message, relevant_chunks, history)
        try:
            answer = ask_llm(messages)
        except Exception as error:
            # show OpenAI's reason (wrong key, no credit, ...) so it is easy to fix
            raise HTTPException(status_code=503, detail=f"Could not get an answer from OpenAI: {error}")

        # 4. the sources are the files and pages of the chunks we used (each one once)
        sources = []
        for chunk in relevant_chunks:
            source = {"file": chunk["file"], "page": chunk["page"]}
            if source not in sources:
                sources.append(source)

        # the model can also decide the context doesn't answer the question
        if answer.lower().replace("’", "'").startswith(I_DONT_KNOW.lower()):
            answer = I_DONT_KNOW
            sources = []

    # 5. remember this question and answer for follow-up questions
    add_message(request.session_id, "user", request.message)
    add_message(request.session_id, "assistant", answer)

    return {"answer": answer, "sources": sources, "session_id": request.session_id}
