I_DONT_KNOW = "I don't know"

SYSTEM_PROMPT = f"""You are a helpful assistant for our company.
- For questions about the documents, use ONLY the context given with the question.
- For questions about a customer (plan, email, city, name), call the get_customer_details tool with the customer id.
- For questions about orders (status, delivery, items, a customer's orders), call
  get_order_status or get_customer_orders.
- You can only read data. You cannot create, change or cancel anything.
- Do not use anything you know from outside the context or the tools.
- If neither the context nor a tool gives the answer, reply with exactly: {I_DONT_KNOW}
Keep the answer short and clear."""


def build_messages(question: str, chunks: list[dict], history: list[dict]) -> list[dict]:
    if chunks:
        context_parts = []
        for chunk in chunks:
            source = chunk["file"] if chunk["page"] is None else f"{chunk['file']}, page {chunk['page']}"
            context_parts.append(f"[{source}]\n{chunk['text']}")
        context = "\n\n".join(context_parts)
    else:
        context = "(no matching text in the documents)"

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    return [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_prompt}]


def says_i_dont_know(answer: str) -> bool:
    if not answer:
        return True
    normalized = answer.lower().replace("’", "'")
    return normalized.startswith(I_DONT_KNOW.lower())
