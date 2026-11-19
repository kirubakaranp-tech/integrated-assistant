from fastapi import APIRouter, HTTPException

from app.config import MAX_DISTANCE, TOP_K
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.embeddings import embed_texts
from app.services.llm import ask_llm
from app.services.memory import add_message, get_history
from app.services.prompt import I_DONT_KNOW, build_messages, says_i_dont_know
from app.services.tools import TOOL_SOURCES
from app.services.vector_store import search

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    history = get_history(request.session_id)

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

    messages = build_messages(request.message, relevant_chunks, history)
    try:
        answer, tools_used = ask_llm(messages)
    except Exception as error:
        raise HTTPException(status_code=503, detail=f"Could not get an answer from OpenAI: {error}")

    found = []
    if tools_used:
        for tool in tools_used:
            tool_name = tool.split("(")[0]
            found.append({"file": TOOL_SOURCES.get(tool_name, tool_name), "page": None})
    else:
        for chunk in relevant_chunks:
            found.append({"file": chunk["file"], "page": chunk["page"]})

    sources = []
    for source in found:
        if source not in sources:
            sources.append(source)

    nothing_found = not relevant_chunks and not tools_used
    if nothing_found or says_i_dont_know(answer):
        answer = I_DONT_KNOW
        sources = []

    add_message(request.session_id, "user", request.message)
    add_message(request.session_id, "assistant", answer)

    return {"answer": answer, "sources": sources, "tools_used": tools_used, "session_id": request.session_id}
