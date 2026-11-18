I_DONT_KNOW = "I don't know"

SYSTEM_PROMPT = f"""You answer questions about the user's documents.
Use ONLY the context given with the question. Do not use anything you know from outside it.
If the context does not contain the answer, reply with exactly: {I_DONT_KNOW}
Keep the answer short and clear."""


def build_messages(question: str, chunks: list[dict], history: list[dict]) -> list[dict]:
    """Build the messages for the model: instructions, earlier conversation, then context + question."""
    context_parts = []
    for chunk in chunks:
        source = chunk["file"] if chunk["page"] is None else f"{chunk['file']}, page {chunk['page']}"
        context_parts.append(f"[{source}]\n{chunk['text']}")
    context = "\n\n".join(context_parts)

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    return [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_prompt}]
